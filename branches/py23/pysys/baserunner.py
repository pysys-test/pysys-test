#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net
"""
Contains the base class used to perform the execution and audit trail reporting of a set of tests. 

Test selection is by default performed through the pysys.py launch script, which locates and 
creates a set of class instances representing the tests to be executed. These are passed to the 
base runner as a list of object references, so that the base runner can then iterate through the 
list to perform the test execution. For more information see the L{pysys.baserunner.BaseRunner} 
API documentation. 

"""
import os.path, stat, math, logging, textwrap, StringIO, thread

from pysys import ThreadedFileHandler, ThreadedStreamHandler
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.threadpool import *
from pysys.utils.loader import import_module
from pysys.utils.fileutils import mkdir
from pysys.basetest import BaseTest
from pysys.process.user import ProcessUser
from pysys.utils.logutils import BaseLogFormatter
from pysys.writer import ConsoleSummaryResultsWriter, ConsoleProgressResultsWriter, BaseSummaryResultsWriter, BaseProgressResultsWriter

global_lock = threading.Lock()

N_CPUS = 1
try:
	# multiprocessing is a new module in 2.6 so we can't assume it
	import multiprocessing
	N_CPUS = multiprocessing.cpu_count()
except ImportError:
	pass

class BaseRunner(ProcessUser):
	"""The base class for executing a set of PySys testcases.

	BaseRunner is the parent class for running a set of PySys system testcases. The runner is instantiated 
	with a list of L{pysys.xml.descriptor.XMLDescriptorContainer} objects detailing the set of testcases to be run. 
	The runner iterates through the descriptor list and for each entry imports the L{pysys.basetest.BaseTest}
	subclass for the testcase, creates an instance of the test class and then calls the setup, execute, validate 
	and cleanup methods of the test class instance. The runner is responsible for ensuring the output 
	subdirectory of each testcase is purged prior to test execution to remove stale output from a previous run, 
	detects any core files produced during execution of a testcase from processes started via the L{pysys.process} 
	module, and performs audit trail logging of the test results on completion of running a set of testcases.
	
	The base runner contains the hook functions L{setup}, L{testComplete}, and L{cleanup} to 
	allow a subclass to perform custom operations prior to the execution of a set of testcases, between the 
	execution of each testcase in a set, and on completion 
	of all testcases respectively. Subclasses are typically used should some global conditions need to be setup 
	prior to the set of testcasess being run (i.e. load data into a shared database, start an external process 
	etc), and subsequently cleaned up after test execution. 
	      
	@ivar mode: The user defined modes to run the tests within
	@type mode: string
	@ivar outsubdir: The directory name for the output subdirectory 
	@type outsubdir: string
	@ivar log: Reference to the logger instance of this class
	@type log: logging.Logger
	@ivar project: Reference to the project details as set on the module load of the launching executable  
	@type project: L{Project}
	
	"""
	
	def __init__(self, record, purge, cycle, mode, threads, outsubdir, descriptors, xargs):
		"""Create an instance of the BaseRunner class.
		
		@param record: Indicates if the test results should be recorded 
		@param purge: Indicates if the output subdirectory should be purged on C{PASSED} result
		@param cycle: The number of times to execute the set of requested testcases
		@param mode: The user defined mode to run the testcases in
		@param threads: The number of worker threads to execute the requested testcases
		@param outsubdir: The name of the output subdirectory
		@param descriptors: List of XML descriptor containers detailing the set of testcases to be run
		@param xargs: The dictionary of additional arguments to be set as data attributes to the class
		
		"""
		ProcessUser.__init__(self)
		
		self.record = record
		self.purge = purge
		self.cycle = cycle
		self.mode = mode
		self.threads = threads
		self.outsubdir = outsubdir
		self.descriptors = descriptors
		self.xargs = xargs
		self.validateOnly = False
		self.setKeywordArgs(xargs)

		if self.threads == 0:
			self.threads = N_CPUS
	
		self.writers = []
		summarywriters = []
		progresswriters = []
		for classname, module, filename, properties in PROJECT.writers:
			module = import_module(module, sys.path)
			writer = getattr(module, classname)(filename)
			for key in list(properties.keys()): setattr(writer, key, properties[key])
			
			if isinstance(writer, BaseSummaryResultsWriter):
				summarywriters.append(writer)
			elif isinstance(writer, BaseProgressResultsWriter):
				progresswriters.append(writer)
			elif self.record: # assume everything else is a record result writer (for compatibility reasons)
				self.writers.append(writer)
		
		# summary writers are always enabled regardless of record mode.
		# allow user to provide their own summary writer in the config, or if not, supply our own
		if summarywriters: 
			self.writers.extend(summarywriters)
		else:
			self.writers.append(ConsoleSummaryResultsWriter())

		if xargs.get('__progressWritersEnabled', False):
			if progresswriters: 
				self.writers.extend(progresswriters)
			else:
				self.writers.append(ConsoleProgressResultsWriter())
		
		# duration and results used to be used for printing summary info, now (in 1.3.0) replaced by 
		# more extensible ConsoleSummaryResultsWriter implementation. Keeping these around for 
		# a bit to allow overlap before removal
		self.duration = 0 # no longer needed
		self.results = {}
		self.__remainingTests = self.cycle * len(self.descriptors)
		
		self.performanceReporters = PROJECT._createPerformanceReporters(self.outsubdir)


	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr()} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. 
		
		@param xargs: A dictionary of the user defined extra arguments
		
		"""
		for key in list(xargs.keys()):
			setattr(self, key, xargs[key])

	
	# methods to allow customer actions to be performed before a test run, after a test, after 
	# a cycle of all tests, and after all cycles
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to execution of a set of testcases.
		
		"""
		pass


	def testComplete(self, testObj, dir):
		"""Test complete method which performs completion actions after execution of a testcase.
		
		The testComplete method performs purging of the output subdirectory of a testcase on completion 
		of the test execution. Purging involves removing all files with a zero file length in order to 
		only include files with content of interest. Should C{self.purge} be set, the purging will remove
		all files (excluding the run.log) on a C{PASSED} outcome of the testcase in order to reduce the 
		on-disk memory footprint when running a large number of tests. Should a custom testComplete for 
		a subclass be required, the BaseRunner testComplete method should first be called.
		
		@param testObj: Reference to the L{pysys.basetest.BaseTest} instance of the test just completed
		@param dir: The directory to perform the purge on
				
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
			for file in os.listdir(dir):
				path = "%s/%s" % (dir, file)
				if PLATFORM in ['sunos', 'linux']:
					size = os.lstat(path)[stat.ST_SIZE]
				else:
					size = os.stat(path)[stat.ST_SIZE]

				if (size == 0) or (removeNonZero and 'run.log' not in file and self.isPurgableFile(path)):
					count = 0
					while count < 3:
						try:
							os.remove(path)
							break
						except Exception:
							time.sleep(0.1)
							count = count + 1

		except OSError as ex:
			log.warning("Caught OSError while cleaning output directory:")
			log.warning(ex)
			log.warning("Output directory may not be completely clean")


	def isPurgableFile(self, path):
		"""Determine if a file should be purged when empty at the end of a test run.

		This method is called by testComplete to provide runners with the ability to veto
		deletion of non-empty files that should always be left in a test's output directory
		even when the test has passed, by returning False from this method. For example this
		could be used to avoid deleting code coverage files. By default this will return True.
		
		@param path: The absolute path of the file to be purged

		"""
		return True


	# perform a test run
	def start(self, printSummary=True):
		"""Start the execution of a set of testcases.
		
		The start method is the main method for executing the set of requested testcases. The set of testcases 
		are executed a number of times determined by the C{self.cycle} attribute. When executing a testcase 
		all output from the execution is saved in the testcase output subdirectory; should C{self.cycle} be 
		set to more than 1, the output subdirectory is further split into cycle[n] directories to sandbox the 
		output from each iteration.
		
		@param printSummary: Ignored, exists only for compatibility reasons. To provide a custom summary printing 
		implementation, specify a BaseSummaryResultsWriter subclass in the <writers> section of your project XML file. 

		@return: Use of this value is deprecated as of 1.3.0. This method returns a dictionary of testcase outcomes, and
		for compatibility reasons this will continue in the short term, but will be removed in a future release. Please
		ignore the return value of start() and use a custom BaseSummaryResultsWriter if you need to customize summarization of
		results.

		"""
		# call the hook to setup prior to running tests
		self.setup()

		# call the hook to setup the test output writers
		for writer in list(self.writers):
			try: writer.setup(numTests=self.cycle * len(self.descriptors), cycles=self.cycle, xargs=self.xargs, threads=self.threads)
			except Exception: 
				log.warn("caught %s setting up %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
				self.writers.remove(writer) # if setup fails, nothing else is going to work

		# create the thread pool if running with more than one thread
		if self.threads > 1: threadPool = ThreadPool(self.threads)

		# loop through each cycle
		self.startTime = time.time()
		
		# by default we allow running tests from different cycles in parallel, 
		# but if the user provided a custom runner with a cycleComplete then 
		# revert to pre-PySys 1.3.0 compatible behaviour and join each cycle 
		# before starting the next, so we can invoke cycleComplete reliably
		concurrentcycles = not hasattr(self, 'cycleComplete')
		
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
						self.containerCallback(thread.get_ident(), container())
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
					if hasattr(self, 'cycleComplete'):
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
		
		# perform cleanup on the test writers - this also takes care of logging summary results
		for writer in self.writers:
			try: writer.cleanup()
			except Exception: log.warn("caught %s cleaning up writer %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
		del self.writers[:]

		# perform clean on the performance reporters
		for perfreporter in self.performanceReporters:
				try: perfreporter.cleanup()
				except Exception as e: log.warn("caught %s performing performance writer cleanup: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

		# call the hook to cleanup after running tests
		self.cleanup()

		# return the results dictionary
		return self.results


	def containerCallback(self, thread, container):
		"""Callback method on completion of running a test.

		Called on completion of running a testcase, either directly by the BaseRunner class (or 
		a sub-class thereof), or from the ThreadPool.wait() when running with more than one worker thread. 
		This method is always invoked from a single thread, even in multi-threaded mode. 

		The method is responsible for calling of the testComplete() method of the runner, recording 
		of the test result to the result writers, and for deletion of the test container object. 

		@param thread: A reference to the calling thread (ignored in 1.3.0 onwards)
		@param container: A reference to the container object that ran the test

		"""
		self.__remainingTests -= 1
		
		if self.threads > 1: 
			# write out cached messages from the worker thread
			sys.stdout.write(container.testFileHandlerStdout.stream.getvalue())
		if stdoutHandler.level >= logging.WARN:
			log.critical("%s: %s (%s)", LOOKUP[container.testObj.getOutcome()], container.descriptor.id, container.descriptor.title)
		
		# call the hook for end of test execution
		self.testComplete(container.testObj, container.outsubdir)
				
		# pass the test object to the test writers is recording
		for writer in self.writers:
			try: writer.processResult(container.testObj, cycle=container.cycle,
									  testStart=container.testStart, testTime=container.testTime)
			except Exception: log.warn("caught %s processing test result by %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
		
		# prompt for continuation on control-C
		if container.kbrdInt == True: self.handleKbrdInt()
	
		# store the result
		self.duration = self.duration + container.testTime
		self.results[container.cycle][container.testObj.getOutcome()].append(container.descriptor.id)
		

	def containerExceptionCallback(self, thread, exc_info):
		"""Callback method for unhandled exceptions thrown when running a test.
		
		@param exc_info: The tuple of values as created from sys.exc_info()
		 
		"""
		log.warn("caught %s from executing test container: %s", exc_info[0], exc_info[1], exc_info=exc_info)


	def handleKbrdInt(self, prompt=True):
		"""Handle a keyboard exception caught during running of a set of testcases.
		
		"""
		if self.__remainingTests <= 0 or os.getenv('PYSYS_DISABLE_KBRD_INTERRUPT_PROMPT', 'false').lower()=='true':
			prompt = False
		
		def finish():
			# perform cleanup on the test writers - this also takes care of logging summary results
			for writer in self.writers:
				try: writer.cleanup()
				except Exception: log.warn("caught %s cleaning up writer %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)
			del self.writers[:]
			if hasattr(self, 'cycleComplete'):
				self.cycleComplete()
			self.cleanup()
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


class TestContainer:
	"""Class used for co-ordinating the execution of a single test case.
	
	"""
	
	def __init__ (self, descriptor, cycle, runner):
		"""Create an instance of the TestContainer class.
		
		@param descriptor: A reference to the testcase descriptor
		@param cycle: The cycle number of the test
		@param runner: A reference to the runner that created this class

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
		self.kbrdInt = False

		
	def __call__(self, *args, **kwargs):
		"""Over-ridden call builtin to allow the class instance to be called directly.
		
		Invoked by thread pool when using multiple worker threads.

		"""		
		exc_info = []
		self.testStart = time.time()
		try:
			# stdout - set this up right at the very beginning to ensure we can see the log output in case any later step fails
			self.testFileHandlerStdout = ThreadedStreamHandler(StringIO.StringIO())
			self.testFileHandlerStdout.setFormatter(PROJECT.formatters.stdout)
			self.testFileHandlerStdout.setLevel(stdoutHandler.level)
			log.addHandler(self.testFileHandlerStdout)

			# set the output subdirectory and purge contents
			if os.path.isabs(self.runner.outsubdir):
				self.outsubdir = os.path.join(self.runner.outsubdir, self.descriptor.id)
			else:
				self.outsubdir = os.path.join(self.descriptor.output, self.runner.outsubdir)

			mkdir(self.outsubdir)
					
			if self.cycle == 0 and not self.runner.validateOnly: 
				self.purgeDirectory(self.outsubdir)
				
			if self.runner.cycle > 1: 
				self.outsubdir = os.path.join(self.outsubdir, 'cycle%d' % (self.cycle+1))
				mkdir(self.outsubdir)

			# run.log handler
			self.testFileHandlerRunLog = ThreadedFileHandler(os.path.join(self.outsubdir, 'run.log'))
			self.testFileHandlerRunLog.setFormatter(PROJECT.formatters.runlog)
			self.testFileHandlerRunLog.setLevel(logging.INFO)
			if stdoutHandler.level == logging.DEBUG: self.testFileHandlerRunLog.setLevel(logging.DEBUG)
			log.addHandler(self.testFileHandlerRunLog)

			log.info(62*"=")
			title = textwrap.wrap(self.descriptor.title.replace('\n','').strip(), 56)
			log.info("Id   : %s", self.descriptor.id, extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
			if len(title)>0:
				log.info("Title: %s", str(title[0]), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
			for l in title[1:]:
				log.info("       %s", str(l), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
			if self.runner.cycle > 1:
				log.info("Cycle: %s", str(self.cycle+1), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
			log.info(62*"=")
		except KeyboardInterrupt:
			self.kbrdInt = True
		
		except Exception:
			exc_info.append(sys.exc_info())
			
		# import the test class
		with global_lock:
			try:
				module = import_module(os.path.basename(self.descriptor.module), [os.path.dirname(self.descriptor.module)], True)
				self.testObj = getattr(module, self.descriptor.classname)(self.descriptor, self.outsubdir, self.runner)
	
			except KeyboardInterrupt:
				self.kbrdInt = True
			
			except Exception:
				exc_info.append(sys.exc_info())
				self.testObj = BaseTest(self.descriptor, self.outsubdir, self.runner)

		for writer in self.runner.writers:
			try: 
				if hasattr(writer, 'processTestStarting'):
					writer.processTestStarting(testObj=self.testObj, cycle=self.cycle)
			except Exception: 
				log.warn("caught %s calling processTestStarting on %s: %s", sys.exc_info()[0], writer.__class__.__name__, sys.exc_info()[1], exc_info=1)

		# execute the test if we can
		try:
			if self.descriptor.state != 'runnable':
				self.testObj.addOutcome(SKIPPED, 'Not runnable', abortOnError=False)
						
			elif self.runner.mode and self.runner.mode not in self.descriptor.modes:
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
						self.testObj.execute()
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
				log.info("Test failure reason: %s", self.testObj.getOutcomeReason(), extra=BaseLogFormatter.tag(LOG_TEST_OUTCOMES, 0))
			log.info("")
			
			self.testFileHandlerRunLog.close()
			log.removeHandler(self.testFileHandlerRunLog)
			log.removeHandler(self.testFileHandlerStdout)
		except Exception: 
			pass
		
		# return a reference to self
		return self
	
	
	# utility methods
	def purgeDirectory(self, dir, delTop=False):
		"""Recursively purge a directory removing all files and sub-directories.
		
		@param dir: The top level directory to be purged
		@param delTop: Indicates if the top level directory should also be deleted

		"""
		try:
			for file in os.listdir(dir):
				path = os.path.join(dir, file)
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
			if delTop: os.rmdir(dir)

		except OSError as ex:
			log.warning("Caught OSError in purgeDirectory():")
			log.warning(ex)
			log.warning("Directory %s may not be completely purged" % dir)


	def detectCore(self, dir):
		"""Detect any core files in a directory (unix systems only), returning C{True} if a core is present.
		
		@param dir: The directory to search for core files
		@return: C{True} if a core detected, None if no core detected
		@rtype: integer 
		"""
		try:
			for file in os.listdir(dir):
				path = os.path.join(dir, file)
				mode = os.stat(path)[stat.ST_MODE]
				if stat.S_ISREG(mode):
					if re.search('^core', file): return True

		except OSError as ex:
			log.warning("Caught OSError in detectCore():")
			log.warning(ex)
