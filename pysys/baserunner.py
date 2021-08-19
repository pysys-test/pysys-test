#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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
import re
import collections
import platform
import shlex
import warnings
import difflib
import importlib

if sys.version_info[0] == 2:
	from StringIO import StringIO
	import Queue as queue
else:
	from io import StringIO
	import queue

import pysys
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.threadpool import *
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists
from pysys.basetest import BaseTest
from pysys.process.user import ProcessUser
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.pycompat import *
from pysys.internal.initlogging import _UnicodeSafeStreamWrapper, pysysLogHandler
from pysys.writer import ConsoleSummaryResultsWriter, ConsoleProgressResultsWriter, BaseSummaryResultsWriter, BaseProgressResultsWriter, ArtifactPublisher
import pysys.utils.allocport

global_lock = threading.Lock() # internal, do not use

class BaseRunner(ProcessUser):
	"""A single instance of the runner class is responsible for orchestrating 
	concurrent execution of tests, and managing setup and cleanup of 
	any resources that are shared across multiple testcases.

	Selection of the tests (and modes) to be run is performed through the ``pysys.py run`` launch script, which locates 
	and creates a set of `pysys.config.descriptor.TestDescriptor` objects based on the command line arguments supplied by 
	the user, and passes it to the runner. 
	After executing any custom `setup` logic the runner's `start` method is responsible for iterating through the 
	descriptor list and for each entry importing and creating an instance of the `BaseTest <pysys.basetest.BaseTest>` subclass 
	named in the descriptor. The runner deletes the contents of the test output directory 
	(to remove any output from previous runs) then calls the test's ``setup``, ``execute``, ``validate`` and ``cleanup`` 
	methods. After each test is complete it performs cleanup of the output directory (removing all files but ``run.log`` 
	if ``purge`` is enabled, or else just files that are empty), detects any core files produced by the test, and 
	invokes any applicable `writers <pysys.writer>` to record the results of each test.

	In most cases the best way to provide runner (i.e. cross-test) shared functionality by creating one or more runner 
	plugins rather than subclassing BaseRunner. 
	Runner plugins provide functionality such as starting of servers and virtual machines to be shared by 
	all tests (not created per-test, for which you'd use a test plugin instead), or to execute extra logic when the 
	runner is setup, and when it is cleaned up after all tests have completed. 
	
	At minimum, a runner plugin is just a class with a setup method::
	
		def setup(self, runner):
			...  
			self.addCleanupFunction(...) # do this if you need to execute code after tests have completed
	
	... and no constructor (or at least no constructor arguments). 
	Optionally it can have public methods and fields for use by testcases using 
	``self.runner.<plugin alias>.XXX``, and for configuration it may have static fields for any plugin configuration 
	properties. Static fields provides the default value (and hence the type) for each property, and then plugin.XXX is 
	assigned the actual value before the plugin's setup method is called. In addition to plugin properties, 
	``pysys run -Xkey=value`` command line overrides can be accessed using the runner's `getXArg()` method. 
	
	Each runner plugin listed in the project configuration 
	with ``<runner-plugin classname="..." alias="..."/>`` is instantiated once by the runner, and can be accessed using 
	``self.<alias>`` on the runner object (if an alias is provided). If you are using a third party PySys runner 
	plugin, consult the documentation for the third party test plugin class to find out what methods and fields are 
	available using ``runner.<alias>.*``. 

	Although plugins are the recommended way to extend the runner, if needed BaseRunner itself can be subclassed, 
	for example:
	
		- override `setup()` if you need to provision resources 
		  (e.g. virtual machines, servers, user accounts, populating a database, etc) that must be shared by many 
		  testcases. The corresponding teardown should be implemented by calling `addCleanupFunction()`. 
		- also override `setup()` if you want to customize the order or contents of the ``self.descriptors`` list of tests to 
		  be run.
		- override `testComplete()` to customize how test output directories are cleaned up at the end of a test's 
		  execution.
	
	Do not override the ``__init__`` constructor when creating a runner subclass; instead, add any initialization logic 
	to your `setup()` method. 
	
	:ivar str ~.outsubdir: The ``--outdir`` for this test run, which gives the directory to be used for the output of 
		each testcase. Typically a relative path, but can also be an absolute path. The basename of this (outDirName) 
		is often used as an identifier for the current test run. 

	:ivar str ~.output: The full path of the output directory that this runner can use for storing global logs, 
		persistent state for servers started in the runner `setup` method, and other data. 
		
		By default the runner output directory is named based on the ``outsubdir`` and located either as a subdirectory 
		of the testRootDir, or if under outsubdir (if it's an absolute path); it can also be overridden using the 
		``pysysRunnerDirName`` project property. 
		
		Writers and runner plugins (e.g. for code coverage reports) can either put their output under this ``output`` 
		directory, or for increased prominence, add ``/..`` which will put their output directly under the testDirRoot 
		(unless an absolute ``--outdir`` path is specified in which case it will go there instead).
		
		Unlike test directories, the runner output directory is not automatically created or cleaned between runs, so 
		if this is required the runner should do it be calling `deleteDir()` and `mkdir()`. 
	
	:ivar logging.Logger ~.log: The Python ``Logger`` instance that should be used to record progress and status 
		information. 
	
	:ivar dict[str,str] ~.runDetails: A dictionary of metadata about this test run that is included in performance
		summary reports and by some writers. 
		
		The default contains a few standard values (currently these include ``outDirName``, ``hostname`` 
		and ``startTime``), and additional items can be added by runner plugins - for example the build number of the 
		application under test. 
		
		Note that it is not permitted to try to change this dictionary after setup has completed. 
	
	:ivar pysys.config.project.Project ~.project: A reference to the singleton project instance containing the 
		configuration of this PySys test project as defined by ``pysysproject.xml``. 
		The project can be used to access information such as the project properties which are shared across all tests 
		(e.g. for hosts and credentials). 

	:ivar bool ~.record: Indicates if the test results should be recorded by the record writer(s), due to 
		the ``--record`` command line argument being specified.
	
	:ivar bool ~.purge: Indicates that all files other than ``run.log`` should be deleted from the output directory 
		unless the test fails; this corresponds to the ``--purge`` command line argument. 

	:ivar int ~.cycle: The number of times each test should be cycled; this corresponds to the ``--cycle`` command line argument. 

	:ivar str ~.mode: No longer used. 

	:ivar int ~.threads: The number of worker threads to execute the requested testcases.

	:ivar list[pysys.config.descriptor.TestDescriptor] ~.descriptors: A list of all the `pysys.config.descriptor.TestDescriptor` test 
		descriptors that are selected for execution by the runner. 

	:ivar dict(str,str|bool) ~.xargs: A dictionary of additional ``-Xkey=value`` user-defined arguments. These are also 
		set as data attributes on the class (but with automatic conversion to match the default value's bool/int/float/list[str]  
		type if a static variable of the same name exists on the class), and for the benefit of other classes 
		such as runner plugins and writers that might want to define their own -X options, see the `getXArg()` method. 

	:ivar bool ~.validateOnly: True if the user has requested that instead of cleaning output directories and running 
		each test, the validation for each test should be re-run on the previous output. 

	:ivar float ~.startTime: The time when the test run started (in seconds since the epoch).
	
	:ivar list[object] ~.runnerPlugins: A list of any plugin instances configured for this runner. This allows plugins 
		to access the functionality of other plugins if needed (for example looking them up by type in this list). 

	:ivar pysys.baserunner.BaseRunner self.runner: Identical to self. Included so that you can write ``self.runner``
		to get a reference to the runner whether self is a BaseTest object or already a BaseRunner object.

	Additional variables that affect only the behaviour of a single method are documented in the associated method. 

	There is also a field for any runner plugins that were configured with an "alias" (see above). 
	
	"""
	
	def __init__(self, record, purge, cycle, mode, threads, outsubdir, descriptors, xargs):
		# we call this here so it's before any user code that should need to allocate ports, but after the 
		# user's custom runner has been imported, making it possible to monkey-patch getEphemeralTCPPortRange() 
		# if needed, e.g. for a new platform. 
		pysys.utils.allocport.initializePortPool()

		ProcessUser.__init__(self)
		self.runner = self

		# Set a sensible default output dir for the runner. Many projects do not actually write 
		# any per-runner files so we do not create (or clean) this path automatically, it's up to 
		# runner subclasses to do so if required. 
		runnerBaseName = self.project.getProperty('pysysRunnerDirName', self.project.expandProperties('__pysys_runner.${outDirName}'))
		if os.path.isabs(outsubdir):
			self.output = os.path.join(outsubdir, runnerBaseName)
		else:
			self.output = os.path.join(self.project.root, runnerBaseName)

		self.record = record
		self.purge = purge
		self.cycle = cycle
		self.threads = threads
		self.outsubdir = outsubdir
		self.descriptors = descriptors
		self.xargs = xargs
		self.validateOnly = False
		self.supportMultipleModesPerRun = True
		if not self.project.getProperty('supportMultipleModesPerRun', True): 
			raise UserError('The deprecated project property supportMultipleModesPerRun=false is no longer supported, please update your tests')

		assert not mode, 'Passing mode= to the runner is no longer supported'

		self.__resultWritingLock = threading.Lock() 
		self.runnerErrors = [] # list of strings

		self.startTime = self.project.startTimestamp
		
		extraOptions = xargs.pop('__extraRunnerOptions', {})
		
		self.setKeywordArgs(xargs)

		if len(descriptors)*cycle == 1: self.threads = 1
		log.info('Running {numDescriptors:,} tests with {threads} threads using PySys {pysysVersion} in Python {pythonVersion} and encoding {encoding}\n'.format(
			numDescriptors=len(self.descriptors), threads=self.threads, pysysVersion=pysys.__version__, pythonVersion='%s.%s.%s'%
			sys.version_info[0:3], encoding=PREFERRED_ENCODING))
		self.writers = []
		summarywriters = []
		progresswriters = []
		self.printLogs = extraOptions['printLogs'] # None if not explicitly set; may be changed by writer.setup()
		self.__printLogsDefault = extraOptions['printLogsDefault']
		
		
		def initWriter(writerclass, writerprops, kwargs={}):
			writer = writerclass(**kwargs) # invoke writer's constructor
			writer.runner = self
			pluginAlias = writerprops.pop('alias', None)

			writer.pluginProperties = writerprops
			pysys.utils.misc.setInstanceVariablesFromDict(writer, writerprops)
			
			if hasattr(writer, 'isEnabled') and not writer.isEnabled(record=self.record): return None
			if pluginAlias: # only set alias if enabled (tests could use the existence of the alias to check if it's enabled e.g. for code cov)
				if hasattr(self, pluginAlias): raise UserError('Alias "%s" for writer conflicts with a field that already exists on this runner; please select a different name'%(pluginAlias))
				setattr(self, pluginAlias, writer)
			return writer
			

		for writerclass, writerprops in self.project.writers:
			writer = initWriter(writerclass, writerprops, kwargs={'logfile':writerprops.pop('file', None)})
			if writer is None: continue
			
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
		
		# special-case this as for maximum usability we want it to run whenever the env var is set regardless of 
		# whether someone thought to add it to their project or not
		annotationsWriter = initWriter(pysys.writer.ConsoleFailureAnnotationsWriter, {})
		if annotationsWriter is not None:
			self.writers.append(annotationsWriter)
		
		if extraOptions.get('progressWritersEnabled', False):
			if progresswriters: 
				self.writers.extend(progresswriters)
			else:
				self.writers.append(initWriter(ConsoleProgressResultsWriter, {}))

		# summary writers are always enabled regardless of record mode. They are executed last. 
		# allow user to provide their own summary writer in the config, or if not, supply our own
		if summarywriters: 
			self.writers.extend(summarywriters)
		else:
			self.writers.append(ConsoleSummaryResultsWriter())
		
		for c in self.project.collectTestOutput:
			if c['outputDir'] == self.project.getProperty('pythonCoverageDir', ''): continue # avoid creating a duplicate collector for this given it'll now be collected by the PythonCoverageWriter
			writer = initWriter(pysys.writer.CollectTestOutputWriter, {
				'destDir':c['outputDir'].replace('@OUTDIR@', self.project.outDirName),
				'fileIncludesRegex':r'.*[/\\]'+fnmatch.translate(c['pattern']), # convert fnmatch into a regex that can be used with .search()
				'outputPattern': c['outputPattern'].replace('@FILENAME@', '@FILENAME@.@FILENAME_EXT@').replace('@OUTDIR@', self.project.outDirName).replace('\\','_').replace('/','_')
			})
			if writer is not None: self.writers.append(writer)

		# also special-case setting this up using just project properties, since prior to 1.6.0 there was no separate writer
		# but only if pythonCoverageDir was explicitly configured in the project
		if not any(isinstance(writer, pysys.writer.PythonCoverageWriter) for writer in self.writers):
			if self.project.getProperty('pythonCoverageDir', ''):
				writer = initWriter(pysys.writer.PythonCoverageWriter, {
					'destDir': self.project.pythonCoverageDir.replace('@OUTDIR@', self.project.outDirName),
					'pythonCoverageArgs':self.project.getProperty('pythonCoverageArgs', u''),
				})
				if writer is not None: self.writers.append(writer)

		self.__artifactWriters = [w for w in self.writers if isinstance(w, ArtifactPublisher)]
		self.__testOutputVisitorWriters = [w for w in self.writers if isinstance(w, pysys.writer.TestOutputVisitor)]

		# duration and results used to be used for printing summary info, now (in 1.3.0) replaced by 
		# more extensible ConsoleSummaryResultsWriter implementation. Keeping these around for 
		# a bit to allow overlap before removal
		self.duration = 0 # no longer needed
		self.results = {}
		
		self.performanceReporters = [] # gets assigned to real value by start(), once runner constructors have all completed
		
		self.__pythonWarnings = 0
		self._configurePythonWarningsHandler()
		
		# (initially) undocumented hook for customizing which jobs the threadpool takes 
		# off the queue and when. Standard implementation is a simple blocking queue. 
		self._testScheduler = queue.Queue()

		# Only do wrapping if we're outputting to console (to avoid making life difficult for tools parsing the output 
		# and because it's not very useful); remove 16chars which is how wide a typical 
		self._testHeaderWrap = 0 if not (sys.stdout) or (not sys.stdout.isatty()) else ( 
			max(40, ((shutil.get_terminal_size()[0] if hasattr(shutil, 'get_terminal_size') else 80) - len('22:34:09 WARN  ')-1)))

		self.runDetails = collections.OrderedDict()
		for p in ['outDirName', 'hostname']:
			self.runDetails[p] = self.project.properties[p]
		if threads>1: self.runDetails['testThreads'] = str(threads)
		self.runDetails['os'] = platform.platform().replace('-',' ')
		
		# escape windows \ chars (which does limit the expressive power, but is likely to be more helpful than not)
		commitCmd = shlex.split(self.project.properties.get('versionControlGetCommitCommand','').replace('\\', '\\\\'))
		import subprocess
		if commitCmd:
			try:
				vcsProcess = subprocess.Popen(commitCmd, cwd=self.project.testRootDir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
				(stdoutdata, stderrdata) = vcsProcess.communicate()
				stdoutdata = stdoutdata.decode(PREFERRED_ENCODING, errors='replace')
				stderrdata = stderrdata.decode(PREFERRED_ENCODING, errors='replace')
				if vcsProcess.returncode != 0:
					raise Exception('Process failed with %d: %s'%(vcsProcess.returncode, stderrdata.strip() or stdoutdata.strip() or '<no output>'))
				
				commit = stdoutdata.strip().split('\n')
				if commit and commit[0]:
					self.runDetails['vcsCommit'] = commit[0]
				else:
					raise Exception('No stdout output')

			except Exception as ex:
				log.info('Failed to get VCS commit using %s: %s', commitCmd, ex)
		if self.xargs: self.runDetails['xargs'] = ', '.join('%s=%s'%(k,v) for k,v in self.xargs.items())

		self.runDetails['startTime'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.startTime))
		
	def __str__(self): 
		""" Returns a human-readable and unique string representation of this runner object containing the runner class, 
		suitable for diagnostic purposes and display to the test author. 
		The format of this string may change without notice. 
		"""
		return self.__class__.__name__ # there's usually only one base runner so class name is sufficient

	def getXArg(self, key, default):
		"""
		Get the value of a ``pysys run -Xkey=value`` argument, with conversion of the value to the required
		int/float/bool/list[str] type as needed (to match the type of the specified default value). The default value 
		returned if no -X argument was provided for this key. 
		
		This method is useful for reading the -X arguments defined by runner plugins or writers. 
		
		.. versionadded:: 1.6.0
		
		:param str key: The name of the -X argument.
		:param bool/int/float/list[str]/str default: The default value to return if the argument was not set on the 
			command line. 
			The type of the default parameter will be used to convert the property value from a string if it is 
			provided (for list[str], comma-separated input is assumed). 
			An exception will be raised if the value is non-empty but cannot be converted to the indicated type. 
		"""
		return pysys.utils.misc.getTypedValueOrDefault(key, self.xargs.get(key, None), default)

	# methods to allow customer actions to be performed before a test run, after a test, after 
	# a cycle of all tests, and after all cycles
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to execution of a set of testcases.
		
		All runner plugins will be setup and instantiated before this method is executed. 
		
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
			for (dirpath, dirnames, filenames) in os.walk(toLongPathSafe(os.path.normpath(dir)), topdown=False):
				deleted = 0
				for file in filenames:
					path = os.path.join(dirpath, file)

					size = None
					try:
						size = os.path.getsize(path)
						if size > 0: # for efficiency, ignore zero byte files
							for visitor in self.__testOutputVisitorWriters:
								if visitor.visitTestOutputFile(testObj, path) is True: break # don't invoke remaining visitors if this one dealt with it
						
					except Exception as ex:
						if not os.path.exists(path): continue
						if size is None: raise # shouldn't happen given the above exists check; the rest of this error handler assumes a problem wiuth the visitor/collection
						
						log.warning("Failed to collect test output file %s: ", path, exc_info=1)
						if not hasattr(self, '_collectErrorAlreadyReported'):
							self.runnerErrors.append('Failed to collect test output from test %s (and maybe others): %s'%(testObj, ex))
							self._collectErrorAlreadyReported = True
					
					# Now proceed with cleaning files
			
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
		"""Decides if the specified non-empty file should be purged (deleted) after a test passes when 
		``--purge`` is enabled.

		By default this will return True, meaning that all files (other than the special case of run.log) 
		will be purged.

		This method is called by `testComplete` to provide runners with the ability to veto
		deletion of non-empty files that should always be left in a test's output directory
		even when the test has passed, by returning False from this method. 
		
		Usually it is best to avoid customizing this method and instead use the ``collect-test-output`` project option 
		to collect any required files (e.g code coverage, performance graphs etc), as collection happens before purging. 
		
		:param str path: The absolute path of the file to be purged. 

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
		
		Do not override this method - instead, override ``setup`` and/or call ``addCleanupFunction`` to customize the behaviour 
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
			self.performanceReporters = [self.project.perfReporterConfig[0](self.project, self.project.perfReporterConfig[1], self.outsubdir, runner=self)]
		
		class PySysPrintRedirector(object):
			def __init__(self):
				self.last = None
				self.encoding = sys.stdout.encoding
				self.log = logging.getLogger('pysys.stdout')
				self.logWarning = True
				self.__origStdout = sys.stdout
			def flush(self): pass
			def write(self, s): 
				if self.logWarning is True:
					self.logWarning = False
					self.log.warning('This test is printing to stdout; it is recommended to use self.log.info(...) instead of print() within PySys tests: \n%s', ''.join(traceback.format_stack()))
				# heuristic for coping with \n happening in a separate write to the message - ignore first newline after a non-newline
				if s!='\n' or self.last=='\n': 
					if isinstance(s, binary_type): s = s.decode(sys.stdout.encoding or PREFERRED_ENCODING, errors='replace')
					self.log.info(s.rstrip())
				self.last = s
			def __getattr__(self, name): return getattr(self.__origStdout, name)
		if self.project.getProperty('redirectPrintToLogger', True):
			sys.stdout = PySysPrintRedirector()

		# before we setup the runner plugins, this is a good time to sanity-check aliases for the test plugins, since we don't want to start testing if this is wrong
		testPluginAliases = set()
		for pluginClass, pluginAlias, pluginProperties in self.project.testPlugins:
			if not pluginAlias: continue
			if hasattr(BaseTest, pluginAlias) or pluginAlias in testPluginAliases: raise UserError('Alias "%s" for test-plugin conflicts with a field that already exists on BaseTest; please select a different name'%(pluginAlias))
			testPluginAliases.add(pluginAlias)

		# call the hook to setup prior to running tests... but setup plugins first. 
		self.runnerPlugins = []
		for pluginClass, pluginAlias, pluginProperties in self.project.runnerPlugins:
			plugin = pluginClass() # if this throws, its a fatal error and we shouldn't run any tests
			plugin.runner = self
			plugin.pluginProperties = pluginProperties
			pysys.utils.misc.setInstanceVariablesFromDict(plugin, pluginProperties, errorOnMissingVariables=True)
			plugin.setup(self)
			
			self.runnerPlugins.append(plugin)
			if not pluginAlias: continue
			if hasattr(self, pluginAlias): raise UserError('Alias "%s" for runner-plugin conflicts with a field that already exists on this runner; please select a different name'%(pluginAlias))
			setattr(self, pluginAlias, plugin)
		
		# see also constructor where we do the same aliasing for writers
		
		self.setup()

		# Now that setup() is done, no-one should be messing with global immutable state (better to not do it at all, but 
		# definitely not after this point)
		self.runDetails = makeReadOnlyDict(self.runDetails)
		pysys.constants.TIMEOUTS = makeReadOnlyDict(pysys.constants.TIMEOUTS)
		self._initialEnviron = os.environ.copy()
		self._initialCwd = os.getcwd()

		# call the hook to setup the test output writers
		self.__remainingTests = self.cycle * len(self.descriptors)
		for writer in list(self.writers):
			try: writer.setup(numTests=self.cycle * len(self.descriptors), cycles=self.cycle, xargs=self.xargs, threads=self.threads, 
				testoutdir=self.outsubdir, runner=self)
			except Exception: 
				log.warning("caught %s setting up %s: %s", sys.exc_info()[0], writer, sys.exc_info()[1], exc_info=1)
				raise # better to fail obviously than to stagger on, but fail to record/update the expected output files, which user might not notice
		
		if self.printLogs is None: self.printLogs = self.__printLogsDefault # default value, unless overridden by cmdline or writer.setup
		
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
					for outcome in OUTCOMES: self.results[cycle][outcome] = []
			
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
					sys.stderr.write("Keyboard interrupt detected... \n")
					self.handleKbrdInt()
				
				if not concurrentcycles:
					if self.threads > 1: 
						try:
							threadPool.wait()
						except KeyboardInterrupt:
							sys.stderr.write("Keyboard interrupt detected during multi-threaded test execution; waiting for running threads to terminate before beginning cleanup... \n")
							threadPool.dismissWorkers(self.threads, True)
							self.handleKbrdInt(prompt=False)
		
					# call the hook for end of cycle if one has been provided
					try:
						self.cycleComplete()
					except KeyboardInterrupt:
						sys.stderr.write("Keyboard interrupt detected while running cycleComplete... \n")
						self.handleKbrdInt()
					except:
						log.warning("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			
			
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

			# perform clean on the performance reporters - before the writers, in case the writers want to do something 
			# with the perf output
			for perfreporter in self.performanceReporters:
					try: perfreporter.cleanup()
					except Exception as ex: 
						log.warning("Caught %s performing performance reporter cleanup: %s", sys.exc_info()[0].__name__, sys.exc_info()[1], exc_info=1)
						fatalerrors.append('Failed to cleanup performance reporter %s: %s'%(repr(perfreporter), ex))
			
			# perform cleanup on the test writers - this also takes care of logging summary results
			with self.__resultWritingLock:
				for writer in self.writers:
					try: 
						writer.cleanup()
					except Exception as ex: 
						log.warning("Writer %s failed during cleanup - %s: %s", writer, sys.exc_info()[0].__name__, sys.exc_info()[1], exc_info=1)
						# might stop results being completely displayed to user
						fatalerrors.append('Writer %s failed during cleanup: %s'%(repr(writer), ex))
				del self.writers[:]
		
			try:
				self.processCoverageData()
			except Exception as ex: 
				log.warning("Caught %s processing coverage data %s: %s", sys.exc_info()[0], writer, sys.exc_info()[1], exc_info=1)
				fatalerrors.append('Failed to process coverage data: %s'%ex)

		finally:
			# call the hook to cleanup after running tests
			try:
				self.cleanup()
			except Exception as ex:
				log.warning("Caught %s performing runner cleanup: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				fatalerrors.append('Failed to cleanup runner: %s'%(ex))

		pysys.utils.allocport.logPortAllocationStats()

		if self.__pythonWarnings:
			log.warning('Python reported %d warnings during execution of tests; is is recommended to do a test run with -Werror and fix them if possible, or filter them out if not (see Python\'s warnings module for details)', self.__pythonWarnings)

		fatalerrors = self.runnerErrors+fatalerrors

		if self._initialEnviron != os.environ:
			log.warning('os.environ has changed while tests were running: \n%s', 
				''.join(difflib.unified_diff(
					['%s=%s\n'%(k,v) for (k,v) in sorted(self._initialEnviron.items())], 
					['%s=%s\n'%(k,v) for (k,v) in sorted(os.environ.items())], 
					'original os.environ', 
					'changed to'
				)))
			if not self.project.getProperty('_ignoreEnvironChangeDuringTestExecution', False): # keep this undocumented as don't really want people using it; correct solution is to initialize libraries which change env vars during runner setup
				fatalerrors.append('Some test has changed the global os.environ of this PySys process; this is extremely unsafe while tests are running - environment changes are only permitted during runner setup')
		if self._initialCwd != os.getcwd():
			fatalerrors.append('Some test has changed the working directory of this PySys process (e.g. with os.chdir()) to "%s"; this is extremely unsafe while tests are running'%os.getcwd())

		if fatalerrors:
			# these are so serious we need to make sure the user notices by returning a failure exit code
			raise UserError('Test runner encountered fatal problems: %s'%'\n\t'.join(fatalerrors))

		# return the results dictionary
		return self.results

	def processCoverageData(self):
		""" Called during cleanup after execution of all tests has completed to allow 
		processing of coverage data (if enabled), for example generating 
		reports etc. 
		
		:deprecated: Instead of overriding this method, create a `pysys.writer.testoutput.CollectTestOutputWriter` subclass, 
			and generate a coverage report in its cleanup method. 
		
		"""
		pass

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
		
		assert container.testObj is not None, 'Fatal error creating test object for %s'%container.descriptor.id # shouldn't happen unless something went very badly wrong
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
				self.printLogs==PrintLogs.FAILURES and testObj.getOutcome().isFailure())): 
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
				log.critical("%s: %s (%s)", testObj.getOutcome(), descriptor.id, descriptor.title)
			
			# pass the test object to the test writers if recording
			for writer in self.writers:
				try: 
					writer.processResult(testObj, cycle=cycle,
										  testStart=testStart, testTime=testDurationSecs, runLogOutput=bufferedoutput)
				except Exception as ex: 
					log.warning("caught %s processing %s test result by %s: %s", sys.exc_info()[0], descriptor.id, writer, sys.exc_info()[1], exc_info=1)
					errors.append('Failed to record test result using writer %s: %s'%(repr(writer), ex))
			
			# store the result
			self.duration = self.duration + testDurationSecs
			self.results[cycle][testObj.getOutcome()].append(descriptor.id)
			
			if errors:
				self.runnerErrors.append('Failed to process results from %s: %s'%(descriptor.id, '; '.join(errors)))


	def publishArtifact(self, path, category):
		"""
		Notifies any interested `pysys.writer.api.ArtifactPublisher` writers about an artifact that they may wish to publish.  

		Called when a file or directory artifact is published (e.g. by another writer).
		
		.. versionadded:: 1.6.0
		
		:param str path: Absolute path of the file or directory. Where possible it is often useful to include 
			the ``outDirName`` in the filename, so that artifacts from multiple test runs/platforms do not clash. 
		:param str category: A string identifying what kind of artifact this is, e.g. 
			"TestOutputArchive" and "TestOutputArchiveDir" (from `pysys.writer.TestOutputArchiveWriter`) or 
			"CSVPerformanceReport" (from `pysys.utils.perfreporter.CSVPerformanceReporter`). 
			If you create your own category, be sure to add an org/company name prefix to avoid clashes.
			Use alphanumeric characters and underscores only. 
		"""
		log.debug('publishArtifact was called with category=%s, path=%s', category, path)
		
		assert category, 'A category must be specified when publishing artifacts (%s)'%path

		badchars = re.sub('[\\w_]+','', category) 
		assert not badchars, 'Unsupported characters "%s" found in category "%s"; please use alphanumeric characters and underscore only'%(badchars, category)
	
		catfilter = self.project.properties.get('publishArtifactCategoryIncludeRegex','')
		if catfilter and not re.match(catfilter, category):
			log.debug('Not publishing artifact as category %s is filtered out by publishArtifactCategoryIncludeRegex'%category)
			return

		path = os.path.normpath(fromLongPathSafe(path)).replace('\\','/')
		for a in self.__artifactWriters:
			a.publishArtifact(path, category)

	def containerExceptionCallback(self, thread, exc_info):
		"""Callback method for unhandled exceptions thrown when running a test.
		
		:meta private: This method would need a better signature before being made public. 
		
		:param exc_info: The tuple of values as created from sys.exc_info()
		 
		"""
		log.warning("caught %s from executing test container: %s", exc_info[0], exc_info[1], exc_info=exc_info)
		self.runnerErrors.append("caught %s from executing test container: %s"%(exc_info[0], exc_info[1]))


	def handleKbrdInt(self, prompt=True): # pragma: no cover (can't auto-test keyboard interrupt handling)
		"""Handle a ``Ctrl+C`` keyboard exception caught during running of a set of testcases.
		
		"""
		if self.__remainingTests <= 0 or os.getenv('PYSYS_DISABLE_KBRD_INTERRUPT_PROMPT', 'false').lower()=='true' or not os.isatty(0):
			prompt = False
		
		def finish():
			self.log.info('Performing runner cleanup after keyboard interrupt')
			
			try:
				# perform cleanup on the test writers - this also takes care of logging summary results
				# this is a stipped down
				with self.__resultWritingLock:
					for writer in self.writers:
						try: 
							writer.cleanup()
						except Exception as ex: 
							log.warning("Writer %s failed during cleanup - %s: %s", writer, sys.exc_info()[0].__name__, sys.exc_info()[1], exc_info=1)
					del self.writers[:]
				
				try:
					self.cycleComplete()
					self.cleanup()
				except Exception: 
					log.warning("caught %s cleaning up runner after interrupt: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			except KeyboardInterrupt:
				log.warning("Keyboard interrupted detected during cleanup; will exit immediately")
			sys.exit(100) # keyboard interrupt

		try:
			if not prompt:
				sys.stderr.write("\nKeyboard interrupt detected, exiting ... \n")
				finish()

			while 1:
				sys.stderr.write("\nKeyboard interrupt detected, continue running remaining tests? [yes|no] ... ")
				line = sys.stdin.readline().strip()
				if line == "y" or line == "yes":
					self.log.info('Keyboard interrupt detected; will try to continue running remaining tests')
					return
				elif line == "n" or line == "no":
					finish()
		except KeyboardInterrupt:
			self.handleKbrdInt(prompt=False) # don't prompt the second time

	def logTestHeader(self, descriptor, cycle, **kwargs):
		"""
		Logs the header for the specified descriptor before a test begin to execute, 
		typically including the testId, title and (if applicable) cycle. 
		
		This method can be overridden if you wish to customize the information that is 
		written to the run.log and console or how it is formatted. 
		"""
		assert not kwargs, 'reserved for future use'
		
		wrap = self._testHeaderWrap - len('Title: ')
		
		# No need to make these fill the entire available width
		log.info("="*62)
		
		log.info("Id:    %s", descriptor.id, extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))

		badchars = re.sub('[%s]+'%pysys.launcher.TEST_ID_CHARS,'', descriptor.idWithoutMode)
		# encourage only underscores, but actually permit . and - too, for compatibility, matching what the launcher does
		if badchars: 
			log.warning('Unsupported characters "%s" found in test id "%s" - please use alphanumeric characters, dot and underscore for test ids', 
				''.join(set(c for c in badchars)), descriptor.idWithoutMode)
		else:
			badchars = re.sub('[%s]+'%pysys.launcher.MODE_CHARS,'', getattr(descriptor, 'mode', None) or '')
			if badchars: log.warning('Unsupported characters "%s" found in test mode "%s" - please use just alphanumeric characters, dot, underscore and equals for modes', 
				''.join(set(c for c in badchars)), descriptor.mode)

		testDir = descriptor.testDir
		if testDir.lower().startswith(os.getcwd().lower()):
			testDir = testDir[len(os.getcwd())+1:]
			if '/' in testDir or '\\' in testDir: # only print if we're running from a higher level directory
				self.log.info('Dir:   %s',  os.path.dirname(testDir)+os.sep, extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))

		title = descriptor.title.replace('\n','').strip()
		if title:
			title = textwrap.wrap(title, wrap) if wrap>0 else [title]
			log.info("Title: %s", (title[0]), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
			for l in title[1:]:
				log.info("       %s", str(l), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		
		if self.cycle > 1: # only log if this runner is doing multiple cycles
			log.info("Cycle: %s", str(cycle+1), extra=BaseLogFormatter.tag(LOG_TEST_DETAILS, 0))
		log.debug('Execution order hint: %s', descriptor.executionOrderHint)
		log.info(62*"=")
	
	def _configurePythonWarningsHandler(self):
		# By default python prints warnings to stderr which is very unhelpful for us
		warningLogger = logging.getLogger('pysys.pythonwarnings')
		def handlePythonWarning(message, category, filename, lineno, file=None, line=None, **kwargs):
			self.__pythonWarnings += 1
			msg = warnings.formatwarning(message, category, filename, lineno, line=None, **kwargs)
			# add a stack trace as otherwise it's not easy to see where in run.py the problem originated, as the 
			# warning is usually logged from as shared base class
			msg = '%s\n%s'%(msg.strip(), ''.join(traceback.format_stack()))
			warningLogger.warning('Python reported a warning: %s', msg)
			
		warnings.showwarning = handlePythonWarning
		

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
		self.testTime = 0.0
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
					if self.descriptor.mode:
						self.outsubdir += '~'+self.descriptor.mode

				# In python2, ensure self.output is a byte string not a unicode string even when --outdir abspath is specified
				if PY2 and isinstance(self.outsubdir, unicode):
					self.outsubdir = self.outsubdir.encode()
					# special-case for custom descriptor loader which gives us \\?\ paths
					if self.outsubdir.startswith(u'\\\\?\\'): self.outsubdir = fromLongPathSafe(self.outsubdir)

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
				runLogEncoding = self.runner.getDefaultFileEncoding('run.log') or PREFERRED_ENCODING
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
				
			logHandlers = pysysLogHandler.getLogHandlersForCurrentThread()
				
			# import the test class
			
			with global_lock:
				BaseTest._currentTestCycle = (self.cycle+1) if (self.runner.cycle > 1) else 0 # backwards compatible way of passing cycle to BaseTest constructor; safe because of global_lock
				try:
					outsubdir = self.outsubdir
					if self.descriptor.module == 'PYTHONPATH': # get a shared test class from the sys.path
						classname = self.descriptor.classname.split('.')
						assert len(classname)>1, 'Please specify a fully qualified classname (e.g. mymodule.classname): %s'%self.descriptor.classname
						module_name, classname = '.'.join(classname[:-1]), classname[-1]
						clazz = getattr(importlib.import_module(module_name), classname)
					else:
						assert self.descriptor.module, repr(self.descriptor.module)
						runpypath = os.path.join(self.descriptor.testDir, self.descriptor.module)
						with open(toLongPathSafe(runpypath), 'rb') as runpyfile:
							runpycode = compile(runpyfile.read(), runpypath, 'exec')
						runpy_namespace = {}
						exec(runpycode, runpy_namespace)
						clazz = runpy_namespace[self.descriptor.classname]
						del runpy_namespace
					self.testObj = clazz(self.descriptor, outsubdir, self.runner)
					
					self.testObj.testPlugins = []
					for pluginClass, pluginAlias, pluginProperties in self.runner.project.testPlugins:
						plugin = pluginClass()
						plugin.runner = self
						plugin.pluginProperties = pluginProperties
						pysys.utils.misc.setInstanceVariablesFromDict(plugin, pluginProperties, errorOnMissingVariables=True)
						plugin.setup(self.testObj)

						self.testObj.testPlugins.append(plugin)

						if not pluginAlias: continue
						if hasattr(self.testObj, pluginAlias): raise UserError('Alias "%s" for test-plugin conflicts with a field that already exists on this test object; please select a different name'%(pluginAlias))
						setattr(self.testObj, pluginAlias, plugin)

		
				except KeyboardInterrupt:
					self.kbrdInt = True
				
				except Exception:
					exc_info.append(sys.exc_info())
				
				if self.testObj is None:
					# We need a BaseTest object, so if the real one failed, we assume/hope there should be no exception 
					# from the PySys BaseTest class and we can use it to hold the error for reporting purposes
					self.testObj = BaseTest(self.descriptor, self.outsubdir, self.runner)
					
				# can't set this in constructor without breaking compatibility, but set it asap after construction
				del BaseTest._currentTestCycle

			for writer in self.runner.writers:
				try: 
					if hasattr(writer, 'processTestStarting'):
						writer.processTestStarting(testObj=self.testObj, cycle=self.cycle)
				except Exception: 
					log.warning("caught %s calling processTestStarting on %s: %s", sys.exc_info()[0], writer, sys.exc_info()[1], exc_info=1)

			# execute the test if we can
			try:
				if self.descriptor.skippedReason:
					self.testObj.addOutcome(SKIPPED, self.descriptor.skippedReason, abortOnError=False)
				
				elif self.descriptor.state != 'runnable':
					self.testObj.addOutcome(SKIPPED, 'Not runnable', abortOnError=False)
							
				elif len(exc_info) > 0:
					self.testObj.addOutcome(BLOCKED, 'Failed to set up test: %s'%exc_info[0][1], abortOnError=False)
					for info in exc_info:
						log.warning("caught %s while setting up test %s: %s", info[0], self.descriptor.id, info[1], exc_info=info)
						
				elif self.kbrdInt:
					log.warning("test interrupt from keyboard")
					self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)
			
				else:
					try:
						if IS_WINDOWS and len(self.testObj.output) > 259 - 40: log.warning('Test output directory is %d characters long; be careful of possible issues caused by the Windows 260-character MAX_PATH limit: %s', 
							len(self.testObj.output), self.testObj.output)
					
						if not self.runner.validateOnly:
							self.testObj.setup()
							log.debug('--- test execute')
							self.testObj.execute()
						log.debug('--- test validate')
						self.testObj.validate()
						
						if self.descriptor.title.endswith('goes here TODO'):
							self.testObj.addOutcome(BLOCKED, 'Test title is still TODO', abortOnError=False)

					except AbortExecution as e:
						del self.testObj.outcome[:]
						self.testObj.addOutcome(e.outcome, e.value, abortOnError=False, callRecord=e.callRecord)
						log.warning('Aborted test due to %s outcome'%e.outcome) # nb: this could be due to SKIPPED

					if self.detectCore(self.outsubdir):
						self.testObj.addOutcome(DUMPEDCORE, 'Core detected in output subdirectory', abortOnError=False)
			
			except KeyboardInterrupt:
				self.kbrdInt = True
				self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)

			except Exception:
				log.warning("caught %s while running test: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				self.testObj.addOutcome(BLOCKED, '%s: %s'%(sys.exc_info()[0].__name__, sys.exc_info()[1]), abortOnError=False)

			# call the cleanup method to tear down the test
			try:
				log.debug('--- test cleanup')
				self.testObj.cleanup()
			
			except KeyboardInterrupt:
				self.kbrdInt = True
				self.testObj.addOutcome(BLOCKED, 'Test interrupt from keyboard', abortOnError=False)
			except UserError as ex: # will already have been logged with stack trace
				self.testObj.addOutcome(BLOCKED, str(ex), abortOnError=False)
			except Exception as ex:
				log.warning("caught %s while cleaning up test: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
				self.testObj.addOutcome(BLOCKED, 'Test cleanup failed: %s (%s)'%(sys.exc_info()[1], sys.exc_info()[0]), abortOnError=False)

			# in case the thread log handlers got overwritten by a naughty test, restore before printing the final summary
			pysysLogHandler.setLogHandlersForCurrentThread(logHandlers)
			
			# the following checks are to give a clear and early indication of a serious cock-up
			if self.runner._initialEnviron != os.environ:
			
				log.warning('os.environ has changed while this test was running: \n%s', 
					''.join(difflib.unified_diff(
						['%s=%s\n'%(k,v) for (k,v) in sorted(self.runner._initialEnviron.items())], 
						['%s=%s\n'%(k,v) for (k,v) in sorted(os.environ.items())], 
						'original os.environ', 
						'changed to'
					)))
				if not self.runner.project.getProperty('_ignoreEnvironChangeDuringTestExecution', False): # keep this undocumented as don't really want people using it; correct solution is to initialize libraries which change env vars during runner setup
					self.testObj.addOutcome(BLOCKED, 'The global os.environ of this PySys process has changed while this test was running; this is extremely unsafe - environment changes are only permitted during runner setup', override=True)
				# Can't reset _initialEnviron here (to make other tests pass) as it's possible the bug was not in this test but in some other test that's still executing, in which case we'd allow it to pass
				
			if self.runner._initialCwd != os.getcwd():
				self.testObj.addOutcome(BLOCKED, 'The working directory of this PySys process was changed to "%s" while this test was running (os.chdir()); this is extremely unsafe'%os.getcwd(), override=True)

			# print summary and close file handles
			self.testTime = math.floor(100*(time.time() - self.testStart))/100.0
			log.info("")
			log.info("Test duration: %s", ('%.2f secs'%self.testTime), extra=BaseLogFormatter.tag(LOG_DEBUG, 0))
			log.info("Test final outcome:  %s", str(self.testObj.getOutcome()), extra=BaseLogFormatter.tag(str(self.testObj.getOutcome()).lower(), 0))
			if self.testObj.getOutcomeReason() and self.testObj.getOutcome() != PASSED:
				log.info("Test outcome reason: %s", self.testObj.getOutcomeReason(), extra=BaseLogFormatter.tag(LOG_TEST_OUTCOMES, 0))
			log.info("")
			
			pysysLogHandler.flush()
			if self.testFileHandlerRunLog: self.testFileHandlerRunLog.stream.close()
			
		except Exception as ex: # should never happen; serious enough to merit recording in both stderr and log
			log.exception('Internal error while executing %s: '%(self.descriptor.id))
			sys.stderr.write('Internal error while executing %s: %s\n'%(self.descriptor.id, ex))
			traceback.print_exc()
			self.runner.runnerErrors.append('Error executing test %s: %s'%(self.descriptor.id, ex))

		finally:
			pysysLogHandler.setLogHandlersForCurrentThread(defaultLogHandlersForCurrentThread)

		# return a reference to self
		return self
	
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
			
