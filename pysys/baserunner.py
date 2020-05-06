#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA


"""
The runner is responsible for orchestrating concurrent execution of the tests, and for setup/cleanup of 
any resources that are shared across multiple tests.

"""
from __future__ import print_function
import os.path, stat, math, logging, textwrap, sys, locale, io, shutil, traceback
import fnmatch

if sys.version_info[0] == 2:
	from StringIO import StringIO
	import Queue as queue
else:
	from io import StringIO
	import queue

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.threadpool import *
from pysys.utils.loader import import_module
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, pathexists
from pysys.basetest import BaseTest
from pysys.process.user import ProcessUser
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.pycompat import *
from pysys.internal.initlogging import _UnicodeSafeStreamWrapper, pysysLogHandler
from pysys.writer import ConsoleSummaryResultsWriter, ConsoleProgressResultsWriter, BaseSummaryResultsWriter, BaseProgressResultsWriter
import pysys.utils.allocport

global_lock = threading.Lock() # internal, do not use

N_CPUS = 1 # internal, do not use
try:
	# multiprocessing is a new module in 2.6 so we can't assume it
	import multiprocessing
	N_CPUS = multiprocessing.cpu_count()
except ImportError:
	pass

class BaseRunner(ProcessUser):
	"""A single instance of the runner class is responsible for orchestrating 
	concurrent execution of tests, and managing setup and cleanup of 
	any resources that are shared across multiple testcases.

	Selection of the tests (and modes) to be run is performed through the ``pysys.py run`` launch script, which locates 
	and creates a set of `pysys.xml.descriptor.TestDescriptor` objects based on the command line arguments supplied by 
	the user, and passes it to the runner. 
	After executing any custom `setup` logic the runner's `start` method is responsible for iterating through the 
	descriptor list and for each entry importing and creating an instance of the `BaseTest <pysys.basetest.BaseTest>` subclass 
	named in the descriptor. The runner deletes the contents of the test output directory 
	(to remove any output from previous runs) then calls the test's ``setup``, ``execute``, ``validate`` and ``cleanup`` 
	methods. After each test is complete it performs cleanup of the output directory (removing all files but ``run.log`` 
	if ``purge`` is enabled, or else just files that are empty), detects any core files produced by the test, and 
	invokes any applicable `writers <pysys.writer>` to record the results of each test.

	This class is the default runner implementation, and it can be subclassed 
	if customizations are needed, for example:
	
		- override `setup` and `cleanup` if you need to provision and tear down resources 
		  (e.g. virtual machines, servers, user accounts, populating a database, etc) that must be shared by many 
		  testcases.
		- override `setup` if you want to customize the order or contents of the ``self.descriptors`` list of tests to 
		  be run.
		- override `testComplete` to customize how test output directories are cleaned up at the end of a test's 
		  execution.
		- override `processCoverageData` to provide support for producing a code coverage report at the end of 
		  executing all tests. 
		
	Do not override the ``__init__`` constructor when creating a runner subclass; instead, add any initialization logic 
	to your `setup()` method. 
	
	:ivar str ~.outsubdir: The directory name for the the output of each testcase. Typically a relative path,
		but can also be an absolute path. 

	:ivar str ~.output: The full path of the output directory that this runner can use for storing any persistent state, 
		e.g. logs for any servers started in the runner `setup` method. The runner output directory is formed based 
		on the ``outsubdir``. 
	
	:ivar logging.Logger ~.log: The Python ``Logger`` instance that should be used to record progress and status 
		information. 
	
	:ivar pysys.xml.project.Project ~.project: A reference to the singleton project instance containing the 
		configuration of this PySys test project as defined by ``pysysproject.xml``. 
		The project can be used to access information such as the project properties which are shared across all tests 
		(e.g. for hosts and credentials). 

	:ivar bool ~.record: Indicates if the test results should be recorded by the record writer(s), due to 
		the ``--record`` command line argument being specified.
	
	:ivar bool ~.purge: Indicates that all files other than ``run.log`` should be deleted from the output directory 
		unless the test fails; this corresponds to the ``--purge`` command line argument. 

	:ivar int ~.cycle: The number of times each test should be cycled; this corresponds to the ``--cycle`` command line argument. 

	:ivar str ~.mode: Legacy parameter used only if ``supportMultipleModesPerRun=False``; specifies the single mode 
		tests will be run with. Ignored unless you have a legacy project. 

	:ivar int ~.threads: The number of worker threads to execute the requested testcases.

	:ivar list[pysys.xml.descriptor.TestDescriptor] ~.descriptors: A list of all the `pysys.xml.descriptor.TestDescriptor` test 
		descriptors that are selected for execution by the runner. 

	:ivar dict(str,str) ~.xargs: A dictionary of additional ``-Xkey=value`` user-defined arguments. These are also 
		set as data attributes on the class.

	:ivar bool ~.validateOnly: True if the user has requested that instead of cleaning output directories and running 
		each test, the validation for each test should be re-run on the previous output. 

	:ivar float ~.startTime: The time when the test run started (in seconds since the epoch).
	
	"""
	
	def __init__(self, record, purge, cycle, mode, threads, outsubdir, descriptors, xargs):
		# we call this here so it's before any user code that should need to allocate ports, but after the 
		# user's custom runner has been imported, making it possible to monkey-patch getEphemeralTCPPortRange() 
		# if needed, e.g. for a new platform. 
		pysys.utils.allocport.initializePortPool()

		ProcessUser.__init__(self)

		# Set a sensible default output dir for the runner. Many projects do not actually write 
		# any per-runner files so we do not create (or clean) this path automatically, it's up to 
		# runner subclasses to do so if required. 
		if os.path.isabs(outsubdir):
			self.output = os.path.join(outsubdir, 'pysys-runner')
		else:
			self.output = os.path.join(self.project.root, 'pysys-runner-%s'%outsubdir)

		self.record = record
		self.purge = purge
		self.cycle = cycle
		self.threads = threads
		self.outsubdir = outsubdir
		self.descriptors = descriptors
		self.xargs = xargs
		self.validateOnly = False
		self.supportMultipleModesPerRun = getattr(self.project, 'supportMultipleModesPerRun', '').lower()=='true'
		if not self.supportMultipleModesPerRun:
			self.mode = mode

		self.__resultWritingLock = threading.Lock() 

		self.startTime = self.project.startTimestamp
		
		extraOptions = xargs.pop('__extraRunnerOptions', {})
		
		self.setKeywordArgs(xargs)

		if self.threads <= 0:
			self.threads = int(os.getenv('PYSYS_DEFAULT_THREADS', N_CPUS)) 
		if self.threads > 1: log.info('Running tests with %d threads', self.threads)
	
		self.writers = []
		summarywriters = []
		progresswriters = []
		self.printLogs = extraOptions['printLogs'] # None if not explicitly set; may be changed by writer.setup()
		for classname, module, filename, properties in self.project.writers:
			module = import_module(module, sys.path)
			writer = getattr(module, classname)(logfile=filename) # invoke writer's constructor
			for key in list(properties.keys()): setattr(writer, key, properties[key])
			
			if hasattr(writer, 'isEnabled') and not writer.isEnabled(record=self.record): continue
			
			if isinstance(writer, BaseSummaryResultsWriter):
				summarywriters.append(writer)
			elif isinstance(writer, BaseProgressResultsWriter):
				progresswriters.append(writer)
			else: # assume everything else is a record result writer (for compatibility reasons)
				# add extra check on self.record for compatibility with old writers that 
				# do not subclass the base writer and therefore would have bypassed 
				# the above isEnabled() check
				if hasattr(writer, 'isEnabled') or self.record: 
					self.writers.append(writer)
		
		if extraOptions.get('progressWritersEnabled', False):
			if progresswriters: 
				self.writers.extend(progresswriters)
			else:
				self.writers.append(ConsoleProgressResultsWriter())

		# summary writers are always enabled regardless of record mode. They are executed last. 
		# allow user to provide their own summary writer in the config, or if not, supply our own
		if summarywriters: 
			self.writers.extend(summarywriters)
		else:
			self.writers.append(ConsoleSummaryResultsWriter())
		
		self.__collectTestOutput = []
		for c in self.project.collectTestOutput:
			c = dict(c)
			assert c['outputDir'], 'collect-test-output outputDir cannot be empty'
			c['outputDir'] = os.path.join(self.project.root, c['outputDir']\
				.replace('@OUTDIR@', os.path.basename(self.outsubdir)) \
				)
			assert os.path.normpath(c['outputDir']) != os.path.normpath(self.project.root), 'Must set outputDir to a new subdirectory'
			self.__collectTestOutput.append(c)
			deletedir(c['outputDir']) # clean output dir between runs
		
		# duration and results used to be used for printing summary info, now (in 1.3.0) replaced by 
		# more extensible ConsoleSummaryResultsWriter implementation. Keeping these around for 
		# a bit to allow overlap before removal
		self.duration = 0 # no longer needed
		self.results = {}
		
		self.performanceReporters = [] # gets assigned to real value by start(), once runner constructors have all completed
		
		# (initially) undocumented hook for customizing which jobs the threadpool takes 
		# off the queue and when. Standard implementation is a simple blocking queue. 
		self._testScheduler = queue.Queue()
		
	def __str__(self): 
		""" Returns a human-readable and unique string representation of this runner object containing the runner class, 
		suitable for diagnostic purposes and display to the test author. 
		The format of this string may change without notice. 
		"""
		return self.__class__.__name__ # there's usually only one base runner so class name is sufficient

	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr()} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. 
		
		:param xargs: A dictionary of the user defined extra arguments
		
		"""
		# in the next major release we'll delete this method and have baserunner inherit the same logic that 
		# basetest uses
		for key in list(xargs.keys()):
			setattr(self, key, xargs[key])

	# methods to allow customer actions to be performed before a test run, after a test, after 
	# a cycle of all tests, and after all cycles
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to execution of a set of testcases.
		
		Always ensure you call the super implementation of setup() before adding any custom logic, using
		``super(MY_RUNNER_CLASS_HERE, self).setup()``. 
		
		"""
		pass


	def testComplete(self, testObj, dir):
		"""Called after a testcase's completion (including finalization of the output and 
		`pysys.basetest.BaseTest.cleanup`) to allow for post-completion tasks such as purging 
		unwanted files from the output directory.
		
		The default implementation removes all files with a zero file length in order to 
		only include files with content of interest. Should ``self.purge`` be ``True``, the purging will remove
		all files (excluding the run.log) on a ``PASSED`` outcome of the testcase in order to reduce the 
		on-disk memory footprint when running a large number of tests. 

		See also `isPurgableFile` which can be used to customize how this method performs purging. 
		
		If you override this method, be sure to call the BaseRunner's implementation afterwards inside a
		``try...finally`` block. Do not put logic which could change the test outcome into this method; instead, 
		use `pysys.basetest.BaseTest.cleanup` for anything which might affect the outcome. 
		
		This method is always invoked from a single thread, even in multi-threaded mode. 
		
		:param testObj: Reference to the `pysys.basetest.BaseTest` instance of the test just completed.
		:param dir: The absolute path of the test output directory to perform the purge on (testObj.output).
				
		"""
		if self.purge:
			removeNonZero = True
			for outcome in testObj.outcome:
				if outcome != PASSED:
					removeNonZero = False
					break
		else:
			removeNonZero = False

		try:
			for (dirpath, dirnames, filenames) in os.walk(toLongPathSafe(dir), topdown=False):
				deleted = 0
				for file in filenames:
					path = os.path.join(dirpath, file)
					for collect in self.__collectTestOutput:
						if fnmatch.fnmatch(os.path.basename(file), collect['pattern']):
							collectdest = os.path.join(mkdir(collect['outputDir']), (collect['outputPattern']
								.replace('@TESTID@', str(testObj))
								.replace('@FILENAME@', os.path.basename(file))
								.replace('\\','_').replace('/','_')
								))
							i = 1
							while pathexists(collectdest.replace('@UNIQUE@', '%d'%(i))):
								i += 1
							collectdest = collectdest.replace('@UNIQUE@', '%d'%(i))
							shutil.copyfile(toLongPathSafe(path), toLongPathSafe(collectdest))
							
					size = os.path.getsize(path)
					
					if (size == 0) or (removeNonZero and 'run.log' not in file and self.isPurgableFile(path)):
						count = 0
						while count < 3:
							try:
								os.remove(path)
								deleted += 1
								break
							except Exception:
								if not os.path.exists(path): break
								time.sleep(0.1)
								count = count + 1
								
				# always try to delete empty directories (just as we do for empty files); 
				# until we have some kind of internal option for disabling this for debugging 
				# purpose only delete dirs when we've just deleted the contents ourselves 
				if removeNonZero or (deleted > 0 and deleted == len(filenames)):
					try:
						os.rmdir(dirpath)
					except Exception as ex:
						# there might be non-empty subdirectories, so don't raise this as an error
						pass
						

		except OSError as ex:
			log.warning("Caught OSError while cleaning output directory after test completed:")
			log.warning(ex)
			log.warning("Output directory may not be completely clean")


	def isPurgableFile(self, path):
		"""Determine if a file should be purged when empty at the end of a test run.

		This method is called by `testComplete` to provide runners with the ability to veto
		deletion of non-empty files that should always be left in a test's output directory
		even when the test has passed, by returning False from this method. For example this
		could be used to avoid deleting code coverage files. By default this will return True.
		
		:param path: The absolute path of the file to be purged

		"""
		return True


	def cycleComplete(self):
		"""Cycle complete method which can optionally be overridden to perform 
		custom operations between the repeated execution of a set of testcases.
		
		The default implementation of this method does nothing. Note that providing 
		an override for this method will result in disabling concurrent test 
		execution across multiple cycles. 
		
		.. warning:: This method is deprecated and overriding it is strongly discouraged as that disables 
			concurrent test execution across cycles. Instead, cleanup should be 
			performed using either `pysys.basetest.BaseTest.cleanup` or `testComplete`.
		"""
		pass


	# perform a test run
	def start(self, printSummary=True):
		"""Starts the execution of a set of testcases.
		
		Do not override this method - instead, override ``setup`` and/or ``cleanup`` to customize the behaviour 
		of this runner. 
		
		The start method is the main method for executing the set of requested testcases. The set of testcases 
		are executed a number of times determined by the C{self.cycle} attribute. When executing a testcase 
		all output from the execution is saved in the testcase output subdirectory; should C{self.cycle} be 
		set to more than 1, the output subdirectory is further split into cycle[n] directories to sandbox the 
		output from each iteration.
		
		:param printSummary: Ignored, exists only for compatibility reasons. To provide a custom summary printing 
			implementation, specify a BaseSummaryResultsWriter subclass in the <writers> section of your project XML file. 

		:return: Use of this value is deprecated as of 1.3.0. This method returns a dictionary of testcase outcomes, and
			for compatibility reasons this will continue in the short term, but will be removed in a future release. Please
			ignore the return value of start() and use a custom BaseSummaryResultsWriter if you need to customize summarization of
			results.

		"""
		if self.project.perfReporterConfig:
			# must construct perf reporters here in start(), since if we did it in baserunner constructor, runner 
			# might not be fully constructed yet
			from pysys.utils.perfreporter import CSVPerformanceReporter
			try:
				self.performanceReporters = [self.project.perfReporterConfig[0](self.project, self.project.perfReporterConfig[1], self.outsubdir, runner=self)]
			except Exception:
				# support for passing kwargs was added in 1.4.0; this branch is a hack to provide compatibility with 1.3.0 custom reporter classes
				CSVPerformanceReporter._runnerSingleton = self
				self.performanceReporters = [self.project.perfReporterConfig[0](self.project, self.project.perfReporterConfig[1], self.outsubdir)]
				del CSVPerformanceReporter._runnerSingleton
		
		class PySysPrintRedirector(object):
			def __init__(self):
				self.last = None
				self.encoding = sys.stdout.encoding
				self.log = logging.getLogger('pysys.stdout')
			def flush(self): pass
			def write(self, s): 
				# heuristic for coping with \n happening in a separate write to the message - ignore first newline after a non-newline
				if s!='\n' or self.last=='\n': 
					if isinstance(s, binary_type): s = s.decode(sys.stdout.encoding or locale.getpreferredencoding(), errors='replace')
					self.log.info(s.rstrip())
				self.last = s
		if getattr(self.project, 'redirectPrintToLogger', False):
			sys.stdout = PySysPrintRedirector()
		
		# call the hook to setup prior to running tests
		self.setup()

		# call the hook to setup the test output writers
		self.__remainingTests = self.cycle * len(self.descriptors)
		for writer in list(self.writers):
			try: writer.setup(numTests=self.cycle * len(self.descriptors), cycles=self.cycle, xargs=self.xargs, threads=self.threads, 
				testoutdir=self.outsubdir, runner=self)
			except Exception: 
				log.warn("caught %s setting up %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
				raise # better to fail obviously than to stagger on, but fail to record/update the expected output files, which user might not notice
		
		if self.printLogs is None: self.printLogs = PrintLogs.ALL # default value, unless overridden by user or writer.setup
		
		# create the thread pool if running with more than one thread
		if self.threads > 1: 
			threadPool = ThreadPool(self.threads, requests_queue=self._testScheduler)

		# loop through each cycle
		
		fatalerrors = []
		
		# by default we allow running tests from different cycles in parallel, 
		# but if the user provided a runner with a cycleComplete that actually 
		# does something then revert to pre-PySys 1.3.0 compatible behaviour and 
		# join each cycle before starting the next, so we can invoke 
		# cycleComplete reliably
		concurrentcycles = type(self).cycleComplete == BaseRunner.cycleComplete
	
		try:

			# for suppressing print-as-we-execute in single-threaded mode (at least until outcome is known)
			singleThreadStdoutDisable = self.threads==1 and self.printLogs!=PrintLogs.ALL
			# the setLogHandlersForCurrentThread invocation below assumes this
			assert pysysLogHandler.getLogHandlersForCurrentThread()==[stdoutHandler] 
				
			for cycle in range(self.cycle):
				# loop through tests for the cycle
				try:
					self.results[cycle] = {}
					for outcome in PRECEDENT: self.results[cycle][outcome] = []
			
					for descriptor in self.descriptors:
						container = TestContainer(descriptor, cycle, self)
						if self.threads > 1:
							request = WorkRequest(container, callback=self.containerCallback, exc_callback=self.containerExceptionCallback)
							threadPool.putRequest(request)
						else:
							if singleThreadStdoutDisable: pysysLogHandler.setLogHandlersForCurrentThread([])
							try:
								singleThreadedResult = container() # run test
							finally:
								if singleThreadStdoutDisable: pysysLogHandler.setLogHandlersForCurrentThread([stdoutHandler])
							self.containerCallback(threading.current_thread().ident, singleThreadedResult)
				except KeyboardInterrupt:
					log.info("test interrupt from keyboard")
					self.handleKbrdInt()
				
				if not concurrentcycles:
					if self.threads > 1: 
						try:
							threadPool.wait()
						except KeyboardInterrupt:
							log.info("test interrupt from keyboard - joining threads ... ")
							threadPool.dismissWorkers(self.threads, True)
							self.handleKbrdInt(prompt=False)
		
					# call the hook for end of cycle if one has been provided
					try:
						self.cycleComplete()
					except KeyboardInterrupt:
						log.info("test interrupt from keyboard")
						self.handleKbrdInt()
					except:
						log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			
			
			# wait for the threads to complete if more than one thread	
			if self.threads > 1: 
				try:
					# this is the method that invokes containerCallback and containerExceptionCallback
					threadPool.wait()
				except KeyboardInterrupt:
					log.info("test interrupt from keyboard - joining threads ... ")
					threadPool.dismissWorkers(self.threads, True)
					self.handleKbrdInt(prompt=False)
				else:
					threadPool.dismissWorkers(self.threads, True)

			for collect in self.__collectTestOutput:
				if pathexists(collect['outputDir']):
					self.log.info('Collected test output to directory: %s', os.path.normpath(collect['outputDir']))
			
			# perform cleanup on the test writers - this also takes care of logging summary results
			with self.__resultWritingLock:
				for writer in self.writers:
					try: writer.cleanup()
					except Exception as ex: 
						log.warn("caught %s cleaning up writer %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
						# might stop results being completely displayed to user
						fatalerrors.append('Failed to cleanup writer %s: %s'%(repr(writer), ex))
				del self.writers[:]
	
			# perform clean on the performance reporters
			for perfreporter in self.performanceReporters:
					try: perfreporter.cleanup()
					except Exception as e: 
						log.warn("caught %s performing performance writer cleanup: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
						fatalerrors.append('Failed to cleanup performance reporter %s: %s'%(repr(perfreporter), ex))
		
			self.processCoverageData()
		finally:
			# call the hook to cleanup after running tests
			try:
				self.cleanup()
			except Exception as ex:
				log.warn("caught %s performing runner cleanup: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				fatalerrors.append('Failed to cleanup runner: %s'%(ex))

		
		if fatalerrors:
			# these are so serious we need to make sure the user notices
			raise Exception('Test runner encountered fatal problems: %s'%'; '.join(fatalerrors))

		# return the results dictionary
		return self.results

	def processCoverageData(self):
		""" Called after execution of all tests has completed to allow 
		processing of coverage data (if enabled), for example generating 
		reports etc. 
		
		The default implementation collates Python coverage data from 
		coverage.py and produces an HTML report. It assumes a project property 
		`pythonCoverageDir` is set to the directory coverage files are 
		collected into, and that PySys was run with `-X pythonCoverage=true`. 
		If a property named pythonCoverageArgs exists then its value will be 
		added to the arguments passed to the run and html report coverage 
		commands. 
		
		Custom runner subclasses may replace or add to this by processing 
		coverage data from other languages, e.g. Java. 		
		"""
		pythonCoverageDir = getattr(self.project, 'pythonCoverageDir', None)
		if self.getBoolProperty('pythonCoverage') and pythonCoverageDir is not None:
			pythonCoverageDir = os.path.join(self.project.root, pythonCoverageDir
				.replace('@OUTDIR@', os.path.basename(self.outsubdir))) # matches collect-test-output logic
			if not pathexists(pythonCoverageDir):
				self.log.info('No Python coverage files were generated.')
			else:
				if self.startPython(['-m', 'coverage', 'combine'], abortOnError=False, 
					workingDir=pythonCoverageDir, stdouterr=pythonCoverageDir+'/python-coverage-combine', 
					disableCoverage=True).exitStatus != 0: return
					
				args = []
				if hasattr(self.project, 'pythonCoverageArgs'):
					args = [a for a in self.project.pythonCoverageArgs.split(' ') if a]
			
				self.startPython(['-m', 'coverage', 'html']+args, abortOnError=False, 
					workingDir=pythonCoverageDir, stdouterr=pythonCoverageDir+'/python-coverage-html', 
					disableCoverage=True)
	

	def containerCallback(self, thread, container):
		"""Callback method on completion of running a test.

		:meta private: Internal method

		Called on completion of running a testcase, either directly by the BaseRunner class (or 
		a sub-class thereof), or from the ThreadPool.wait() when running with more than one worker thread. 
		This method is always invoked from a single thread, even in multi-threaded mode. 

		The method is responsible for calling of the testComplete() method of the runner, recording 
		of the test result to the result writers, and for deletion of the test container object. 

		:param thread: A reference to the calling thread (ignored in 1.3.0 onwards)
		:param container: A reference to the container object that ran the test

		"""
		# Most of the logic lives in writeTestOutcome, this method just contains the bits that only make 
		# sense if this is a "standard" test executed by our scheduler. Custom runners can use writeTestOutcome 
		# to add additional test results (e.g. to expand out individual unit test results)
		
		self.__remainingTests -= 1
		
		self.reportTestOutcome(
			testObj=container.testObj,
			cycle=container.cycle,
			testStart=container.testStart,
			testDurationSecs=container.testTime,
			runLogOutput=container.testFileHandlerStdoutBuffer.getvalue())
		
		# prompt for continuation on control-C
		if container.kbrdInt == True: self.handleKbrdInt()
		
		# call the hook for end of test execution
		self.testComplete(container.testObj, container.outsubdir)

	def reportTestOutcome(self, testObj, testStart, testDurationSecs, cycle=0, runLogOutput=u'', **kwargs):
		"""
		Records the result of a completed test, including notifying any configured writers, and writing the 
		specified output to the console (if permitted by the `constants.PrintLogs` setting). 
		
		It is not supported to override this method. 
		
		This method is called at the end of each test's execution, but you can also call it (from any thread) 
		to add additional test results that are not in this runner's set of descriptors, for example to 
		expand out individual unit test results as if each had their own PySys test. 
		
		:meta private: Currently internal; will make this public in a future release.

		:param pysys.basetest.BaseTest testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. 
			The writer can extract data from this object but should not store a reference to it. 
			The ``testObj.descriptor.id`` indicates the test that ran. 
		:param int cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		:param float testDurationSecs: Duration of the test in seconds as a floating point number. 
		:param float testStart: The time when the test started. 
		:param str runLogOutput: The logging output written to run.log, as a unicode character string. 
		:param kwargs: Additional keyword arguments may be added in future releases. 

		"""
		errors = []
		descriptor = testObj.descriptor
		
		bufferedoutput = runLogOutput

		with self.__resultWritingLock:
			# print if we need to AND haven't already done so using single-threaded ALL print-as-we-go
			if runLogOutput and ((self.printLogs==PrintLogs.ALL and self.threads > 1) or (
				self.printLogs==PrintLogs.FAILURES and testObj.getOutcome() in FAILS)): 
				try:
					# write out cached messages from the worker thread to stdout
					# (use the stdoutHandler stream which includes coloring redirections if applicable, 
					# but not print redirection which we don't want; also includes the 
					# appropriate _UnicodeSafeStreamWrapper). 
					stdoutHandler.stream.write(bufferedoutput)
					
				except Exception as ex:
					# first write a simple message without any unusual characters, in case nothing else can be printed
					sys.stdout.write('ERROR - failed to write buffered test output for %s\n'%descriptor.id)
					errors.append('Failed to write buffered test output')
					log.exception("Failed to write buffered test output for %s: "%descriptor.id)
					
			if self.printLogs != PrintLogs.NONE and stdoutHandler.level >= logging.WARN:
				# print at least some information even if logging is turned down; 
				# but if in PrintLogs.NONE mode truly do nothing, as there may be a CI writer doing a customized variant of this
				log.critical("%s: %s (%s)", LOOKUP[testObj.getOutcome()], descriptor.id, descriptor.title)
			
			# pass the test object to the test writers if recording
			for writer in self.writers:
				try: 
					writer.processResult(testObj, cycle=cycle,
										  testStart=testStart, testTime=testDurationSecs, runLogOutput=bufferedoutput)
				except Exception as ex: 
					log.warn("caught %s processing %s test result by %s: %s", sys.exc_info()[0], descriptor.id, writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
					errors.append('Failed to record test result using writer %s: %s'%(repr(writer), ex))
			
			# store the result
			self.duration = self.duration + testDurationSecs
			self.results[cycle][testObj.getOutcome()].append(descriptor.id)
			
			if errors:
				raise Exception('Failed to process results from %s: %s'%(descriptor.id, '; '.join(errors)))

	def containerExceptionCallback(self, thread, exc_info):
		"""Callback method for unhandled exceptions thrown when running a test.
		
		:meta private: This method would need a better signature before being made public. 
		
		:param exc_info: The tuple of values as created from sys.exc_info()
		 
		"""
		log.warn("caught %s from executing test container: %s", exc_info[0], exc_info[1], exc_info=exc_info)


	def handleKbrdInt(self, prompt=True): # pragma: no cover (can't auto-test keyboard interrupt handling)
		"""Handle a ``Ctrl+C`` keyboard exception caught during running of a set of testcases.
		
		"""
		if self.__remainingTests <= 0 or os.getenv('PYSYS_DISABLE_KBRD_INTERRUPT_PROMPT', 'false').lower()=='true' or not os.isatty(0):
			prompt = False
		
		def finish():
			# perform cleanup on the test writers - this also takes care of logging summary results
			for writer in self.writers:
				try: writer.cleanup()
				except Exception: log.warn("caught %s cleaning up writer %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
			del self.writers[:]
			try:
				self.cycleComplete()
				self.cleanup()
			except Exception: 
				log.warn("caught %s cleaning up runner after interrupt %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
			sys.exit(1)

		try:
			if not prompt:
				print("Keyboard interrupt detected, exiting ... ")
				finish()

			while 1:
				sys.stdout.write("\nKeyboard interrupt detected, continue running tests? [yes|no] ... ")
				line = sys.stdin.readline().strip()
				if line == "y" or line == "yes":
					break
				elif line == "n" or line == "no":
					finish()
		except KeyboardInterrupt:
			self.handleKbrdInt(prompt)

	def logTestHeader(self, descriptor, cycle, **kwargs):
		"""
		Logs the header for the specified descriptor before a test begin to execute, 
		typically including the testId, title and (if applicable) cycle. 
		
		This method can be overridden if you wish to customize the information that is 
		written to the run.log and console or how it is formatted. 
		"""
		assert not kwargs, 'reserved for future use'
		log.info(62*"=")
		title = textwrap.wrap(descriptor.title.replace('\n','').strip(), 56)
		log.info("Id   : %s", descriptor.id, extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		if len(title)>0:
			log.info("Title: %s", str(title[0]), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		for l in title[1:]:
			log.info("       %s", str(l), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		if self.cycle > 1: # only log if this runner is doing multiple cycles
			log.info("Cycle: %s", str(cycle+1), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		log.debug('Execution order hint: %s', descriptor.executionOrderHint)
		log.info(62*"=")

class TestContainer(object):
	"""Internal class added to the work queue and used for co-ordinating the execution of a single test case.
	
	:meta private:
	"""

	__purgedOutputDirs = set() # static field
	
	def __init__ (self, descriptor, cycle, runner):
		"""Create an instance of the TestContainer class.
		
		:param descriptor: A reference to the testcase descriptor
		:param cycle: The cycle number of the test
		:param runner: A reference to the runner that created this class

		"""
		self.descriptor = descriptor
		self.cycle = cycle
		self.runner = runner
		self.outsubdir = ""
		self.testObj = None
		self.testStart = None
		self.testTime = None
		self.testBuffer = []
		self.testFileHandlerRunLog = None
		self.testFileHandlerStdout = None
		self.testFileHandlerStdoutBuffer = StringIO() # unicode characters written to the output for this testcase
		self.kbrdInt = False

	def __str__(self): return self.descriptor.id+('' if self.runner.cycle <= 1 else '.cycle%03d'%(self.cycle+1))
	
	@staticmethod
	def __onDeleteOutputDirError(function, path, excinfo):
		if function==os.rmdir:
			# Useful to tolerate this since people foten keep a cmd window/shell/tool open on test output directories, 
			# and while we wouldn't want to leave files around, empty directories don't usually cause problems. 
			# In rare cases where someone cares they could explicitly verify the directory doesn't exist at the start of 
			# their run() method. 
			log.debug('Ignoring failure to delete test output directory before running test: %s', path)
		else:
			raise excinfo[1] # re-raise the original error
	
	def __call__(self, *args, **kwargs):
		"""Over-ridden call builtin to allow the class instance to be called directly.
		
		Invoked by thread pool when using multiple worker threads.

		"""		
		exc_info = []
		self.testStart = time.time()
		
		defaultLogHandlersForCurrentThread = pysysLogHandler.getLogHandlersForCurrentThread()
		try:
			try:
				# stdout - set this up right at the very beginning to ensure we can see the log output in case any later step fails
				# here we use UnicodeSafeStreamWrapper to ensure we get a buffer of unicode characters (mixing chars+bytes leads to exceptions), 
				# from any supported character (utf-8 being pretty much a superset of all encodings)
				self.testFileHandlerStdout = logging.StreamHandler(_UnicodeSafeStreamWrapper(self.testFileHandlerStdoutBuffer, writebytes=False, encoding='utf-8'))
				self.testFileHandlerStdout.setFormatter(self.runner.project.formatters.stdout)
				self.testFileHandlerStdout.setLevel(stdoutHandler.level)
				pysysLogHandler.setLogHandlersForCurrentThread(defaultLogHandlersForCurrentThread+[self.testFileHandlerStdout])

				# set the output subdirectory and purge contents; must be unique per mode (but not per cycle)
				if os.path.isabs(self.runner.outsubdir):
					self.outsubdir = os.path.join(self.runner.outsubdir, self.descriptor.id)
					# don't need to add mode to this path as it's already in the id
				else:
					self.outsubdir = os.path.join(self.descriptor.testDir, self.descriptor.output, self.runner.outsubdir)
					if self.runner.supportMultipleModesPerRun and self.descriptor.mode:
						self.outsubdir += '~'+self.descriptor.mode

				try:
					if not self.runner.validateOnly: 
						if self.runner.cycle <= 1: 
							deletedir(self.outsubdir, onerror=TestContainer.__onDeleteOutputDirError)
						else:
							# must use lock to avoid deleting the parent dir after we've started creating outdirs for some cycles
							with global_lock:
								if self.outsubdir not in TestContainer.__purgedOutputDirs:
									deletedir(self.outsubdir, onerror=TestContainer.__onDeleteOutputDirError)
									TestContainer.__purgedOutputDirs.add(self.outsubdir)
				except Exception as ex:
					raise Exception('Failed to clean test output directory before starting test: %s'%ex)
				
				if self.runner.cycle > 1: 
					self.outsubdir = os.path.join(self.outsubdir, 'cycle%d' % (self.cycle+1))
				mkdir(self.outsubdir)
				initialOutputFiles = os.listdir(toLongPathSafe(self.outsubdir))

				# run.log handler
				runLogEncoding = self.runner.getDefaultFileEncoding('run.log') or locale.getpreferredencoding()
				self.testFileHandlerRunLog = logging.StreamHandler(_UnicodeSafeStreamWrapper(
					io.open(toLongPathSafe(os.path.join(self.outsubdir, 'run.log')), 'a', encoding=runLogEncoding), 
					writebytes=False, encoding=runLogEncoding))
				self.testFileHandlerRunLog.setFormatter(self.runner.project.formatters.runlog)
				# unlike stdout, we force the run.log to be _at least_ INFO level
				self.testFileHandlerRunLog.setLevel(logging.INFO)
				if stdoutHandler.level == logging.DEBUG: self.testFileHandlerRunLog.setLevel(logging.DEBUG)
				pysysLogHandler.setLogHandlersForCurrentThread(defaultLogHandlersForCurrentThread+[self.testFileHandlerStdout, self.testFileHandlerRunLog])

				self.runner.logTestHeader(self.descriptor, self.cycle)
				
				# this often doesn't matter, but it's worth alerting the user as in rare cases it could cause a test failure
				if initialOutputFiles and not self.runner.validateOnly:
					log.warning('Some directories from a previous run could not be deleted from the output directory before starting this test: %s', ', '.join(initialOutputFiles))
			except KeyboardInterrupt:
				self.kbrdInt = True
			
			except Exception:
				exc_info.append(sys.exc_info())
				
			# import the test class
			with global_lock:
				BaseTest._currentTestCycle = (self.cycle+1) if (self.runner.cycle > 1) else 0 # backwards compatible way of passing cycle to BaseTest constructor; safe because of global_lock
				try:
					# replace any ${...} project properties in the module name
					if '${' in self.descriptor.module:
						self.descriptor.module =  re.sub(r'[$][{]([^}]+)[}]', 
							lambda match: self.runner.project.properties[match.group(1)], self.descriptor.module)
					if not self.descriptor.module.endswith('.py'): self.descriptor.module += '.py'
					runpypath = os.path.join(self.descriptor.testDir, self.descriptor.module)
					with open(runpypath, 'rb') as runpyfile:
						runpycode = compile(runpyfile.read(), runpypath, 'exec')
					runpy_namespace = {}
					exec(runpycode, runpy_namespace)
					outsubdir = self.outsubdir
					self.testObj = runpy_namespace[self.descriptor.classname](self.descriptor, outsubdir, self.runner)
					del runpy_namespace
		
				except KeyboardInterrupt:
					self.kbrdInt = True
				
				except Exception:
					exc_info.append(sys.exc_info())
					self.testObj = BaseTest(self.descriptor, self.outsubdir, self.runner)
				# can't set this in constructor without breaking compatibility, but set it asap after construction
				del BaseTest._currentTestCycle

			for writer in self.runner.writers:
				try: 
					if hasattr(writer, 'processTestStarting'):
						writer.processTestStarting(testObj=self.testObj, cycle=self.cycle)
				except Exception: 
					log.warn("caught %s calling processTestStarting on %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)

			# execute the test if we can
			try:
				if self.descriptor.skippedReason:
					self.testObj.addOutcome(SKIPPED, self.descriptor.skippedReason, abortOnError=False)
				
				elif self.descriptor.state != 'runnable':
					self.testObj.addOutcome(SKIPPED, 'Not runnable', abortOnError=False)
							
				elif self.runner.supportMultipleModesPerRun==False and self.runner.mode and self.runner.mode not in self.descriptor.modes:
					self.testObj.addOutcome(SKIPPED, "Unable to run test in %s mode"%self.runner.mode, abortOnError=False)
				
				elif len(exc_info) > 0:
					self.testObj.addOutcome(BLOCKED, 'Failed to set up test: %s'%exc_info[0][1], abortOnError=False)
					for info in exc_info:
						log.warn("caught %s while setting up test %s: %s", info[0], self.descriptor.id, info[1], exc_info=info)
						
				elif self.kbrdInt:
					log.warn("test interrupt from keyboard")
					self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)
			
				else:
					try:
						if not self.runner.validateOnly:
							self.testObj.setup()
							log.debug('--- test execute')
							self.testObj.execute()
						log.debug('--- test validate')
						self.testObj.validate()
					except AbortExecution as e:
						del self.testObj.outcome[:]
						self.testObj.addOutcome(e.outcome, e.value, abortOnError=False, callRecord=e.callRecord)
						log.warn('Aborted test due to abortOnError set to true')

					if self.detectCore(self.outsubdir):
						self.testObj.addOutcome(DUMPEDCORE, 'Core detected in output subdirectory', abortOnError=False)
			
			except KeyboardInterrupt:
				self.kbrdInt = True
				self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)

			except Exception:
				log.warn("caught %s while running test: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				self.testObj.addOutcome(BLOCKED, '%s (%s)'%(sys.exc_info()[1], sys.exc_info()[0]), abortOnError=False)
		
			# call the cleanup method to tear down the test
			try:
				log.debug('--- test cleanup')
				self.testObj.cleanup()
			
			except KeyboardInterrupt:
				self.kbrdInt = True
				self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)
				
			# print summary and close file handles
			try:
				self.testTime = math.floor(100*(time.time() - self.testStart))/100.0
				log.info("")
				log.info("Test duration: %s", ('%.2f secs'%self.testTime), extra=BaseLogFormatter.tag(LOG_DEBUG, 0))
				log.info("Test final outcome:  %s", LOOKUP[self.testObj.getOutcome()], extra=BaseLogFormatter.tag(LOOKUP[self.testObj.getOutcome()].lower(), 0))
				if self.testObj.getOutcomeReason() and self.testObj.getOutcome() != PASSED:
					log.info("Test outcome reason: %s", self.testObj.getOutcomeReason(), extra=BaseLogFormatter.tag(LOG_TEST_OUTCOMES, 0))
				log.info("")
				
				pysysLogHandler.flush()
				if self.testFileHandlerRunLog: self.testFileHandlerRunLog.stream.close()
			except Exception as ex: # really should never happen so if it does make sure we know why
				sys.stderr.write('Error in callback for %s: %s\n'%(self.descriptor.id, ex))
				traceback.print_exc()
			
			# return a reference to self
			return self
		finally:
			pysysLogHandler.setLogHandlersForCurrentThread(defaultLogHandlersForCurrentThread)
	
	# utility methods
	def purgeDirectory(self, dir, delTop=False): # pragma: no cover (deprecated, no longer used)
		"""Recursively purge a directory removing all files and sub-directories.
		
		:param dir: The top level directory to be purged
		:param delTop: Indicates if the top level directory should also be deleted

		@deprecated: Use L{pysys.utils.fileutils.deletedir} instead. 
		"""
		try:
			for file in os.listdir(toLongPathSafe(dir)):
				path = toLongPathSafe(os.path.join(dir, file))
				if PLATFORM in ['sunos', 'linux']:
					mode = os.lstat(path)[stat.ST_MODE]
				else:
					mode = os.stat(path)[stat.ST_MODE]
			
				if stat.S_ISLNK(mode):
					os.unlink(path)
				if stat.S_ISREG(mode):
					os.remove(path)
				elif stat.S_ISDIR(mode):
					self.purgeDirectory(path, delTop=True)
			if delTop: os.rmdir(toLongPathSafe(dir))

		except OSError as ex:
			log.warning("Caught OSError in purgeDirectory():")
			log.warning(ex)
			log.warning("Directory %s may not be completely purged" % dir)


	def detectCore(self, dir):
		"""Detect any core files in a directory (unix systems only), returning C{True} if a core is present.
		
		:param dir: The directory to search for core files
		:return: C{True} if a core detected, None if no core detected
		:rtype: integer 
		"""
		try:
			for file in os.listdir(toLongPathSafe(dir)):
				path = toLongPathSafe(os.path.join(dir, file))
				mode = os.stat(path)[stat.ST_MODE]
				if stat.S_ISREG(mode):
					if re.search('^core', file): return True

		except OSError as ex:
			log.warning("Caught OSError in detectCore():")
			log.warning(ex)
