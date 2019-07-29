#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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
Contains the L{BaseTest} class that is subclassed by each individual testcase, 
provides most of the assertion methods, and itself subclasses L{pysys.process.user.ProcessUser}. 

For more information see the L{pysys.basetest.BaseTest} API documentation. 

@undocumented: TEST_TEMPLATE
"""
import os.path, time, threading, logging

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filegrep import filegrep
from pysys.utils.filegrep import lastgrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.utils.threadutils import BackgroundThread
from pysys.process.monitor import ProcessMonitorTextFileHandler
from pysys.process.monitorimpl import DEFAULT_PROCESS_MONITOR
from pysys.manual.ui import ManualTester
from pysys.process.user import ProcessUser
from pysys.utils.pycompat import *
from pysys.utils.fileutils import pathexists

TEST_TEMPLATE = '''%s
%s

class %s(%s):
	def execute(self):
		pass

	def validate(self):
		pass
'''


class BaseTest(ProcessUser):
	"""The base class for all PySys testcases.

	BaseTest is the parent class of all PySys system testcases. The class provides utility functions for 
	cross-platform process management and manipulation, test timing, and test validation. Any PySys testcase 
	should inherit from the base test and provide an implementation of the abstract L{execute} method 
	defined in this class. Child classes can also overide the L{setup}, L{cleanup} and L{validate} 
	methods of the class to provide custom setup and cleanup actions for a particual test, and to perform 
	all validation steps in a single method should this prove logically more simple.
	
	Execution of a PySys testcase is performed through an instance of the L{pysys.baserunner.BaseRunner}
	class, or a subclass thereof. The base runner instantiates an instance of the testcase, and then calls 
	the C{setup}, C{execute}, C{validate} and C{cleanup} methods of the instance. All processes started during 
	the test execution are reference counted within the base test, and terminated within the C{cleanup} method.
	
	Validation of the testcase is through the C{assert*} methods. Execution of many methods appends an outcome 
	to the outcome data structure maintained by the ProcessUser base class, thus building up a record of the 
	individual validation outcomes. Several potential outcomes are supported by the PySys framework 
	(C{SKIPPED}, C{BLOCKED}, C{DUMPEDCORE}, C{TIMEDOUT}, C{FAILED}, C{NOTVERIFIED}, and C{PASSED}) and the 
	overall outcome of the testcase is determined using aprecedence order of the individual outcomes. 

	@ivar mode: The user defined mode the test is running within. Subclasses can use this in conditional checks
	           to modify the test execution based upon the mode.
	@type mode: string
	@ivar input: Full path to the input directory of the testcase. This is used both by the class and its 
	            subclasses to locate the default directory containing all input data to the testcase, as defined
	            in the testcase descriptor.  
	@type input: string
	@ivar output: Full path to the output sub-directory of the testcase. This is used both by the class and its 
				subclasses to locate the default directory for output produced by the testcase. Note that this 
				is the actual directory where all output is written, as modified from that defined in the testcase 
				descriptor to accomodate for the sub-directory used within this location to sandbox concurrent 
				execution of the test, and/or to denote the run number. 
	@type output: string
	@ivar reference: Full path to the reference directory of the testcase. This is used both by the class and its 
	            subclasses to locate the default directory containing all reference data to the testcase, as defined
	            in the testcase descriptor.  
	@type reference: string
	@ivar log: Reference to the logger instance of this class
	@type log: logging.Logger
	@ivar project: Reference to the project details as set on the module load of the launching executable  
	@type project: L{Project}
	@ivar descriptor: Information about this testcase, with fields such as id, title, etc
	@type descriptor: L{pysys.xml.descriptor.TestDescriptor}
	@ivar testCycle: The cycle in which this test is running. Numbering starts from 1 in a multi-cycle test run. 
	The special value of 0 is used to indicate that this is not part of a multi-cycle run. 
	@type testCycle: int
		
	"""
	
	def __init__ (self, descriptor, outsubdir, runner):
		"""Create an instance of the BaseTest class.
		
		@param descriptor: The descriptor for the test giving all test details
		@param outsubdir: The output subdirectory the test output will be written to
		@param runner: Reference to the runner responsable for executing the testcase
		
		"""
		ProcessUser.__init__(self)
		self.descriptor = descriptor
		self.input = os.path.join(descriptor.testDir, descriptor.input)
		self.output = os.path.join(descriptor.testDir, descriptor.output, outsubdir)
		self.reference = os.path.join(descriptor.testDir, descriptor.reference)
		self.runner = runner
		if runner.supportMultipleModesPerRun:
			self.mode = descriptor.mode
		else:
			self.mode = runner.mode 
		self.setKeywordArgs(runner.xargs)
		self.monitorList = []
		self.__backgroundThreads = []
		self.manualTester = None
		self.resources = []
		self.testCycle = getattr(BaseTest, '_currentTestCycle', None) # set when constructed by runner
	
	def __str__(self): 
		""" Returns a human-readable and unique string representation of this test object containing the descriptor id 
		and a suffix indicating the cycle number if this is a multi-cycle test run. 
		
		This is suitable for diagnostic purposes and display to the test author. The format of this string may 
		change without notice. 
		"""
		return ('%s.cycle%03d'%(self.descriptor.id, self.testCycle)) if self. testCycle else self.descriptor.id

	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the test class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. This is used so that subclasses can define default values of 
		data attributes, which can be overriden on instantiation e.g. using the -X options to the 
		runTest.py launch executable.
		
		If an existing attribute is present on this test class (typically a 
		static class variable) and it has a type of bool, int or float, then 
		any -X options will be automatically converted from string to that type. 
		This facilitates providing default values for parameters such as 
		iteration count or timeouts as static class variables with the 
		possibility of overriding on the command line, for example `-Xiterations=123`. 
		
		@param xargs: A dictionary of the user defined extra arguments
		
		"""
		for key in list(xargs.keys()):
			val = xargs[key]
			basetestDefaultValue = getattr(self, key, None) # most of the time these will not be on the basetest
			if basetestDefaultValue is not None and isstring(val):
				# attempt type coersion to keep the type the same
				if basetestDefaultValue == True or basetestDefaultValue == False:
					val = val.lower()=='true'
				elif isinstance(basetestDefaultValue, int):
					val = int(val)
				elif isinstance(basetestDefaultValue, float):
					val = float(val)
			setattr(self, key, val)

			
	# test methods for execution, validation and cleanup. The execute method is
	# abstract and must be implemented by a subclass. 
	def setup(self):
		"""Setup method which may optionally be overridden to perform custom setup operations prior to test execution.
		
		"""
		pass		


	def execute(self):
		"""Execute method which must be overridden to perform the test execution steps.
		
		@raises NotImplementedError:  Raised exeception should the method not be overridden
		"""
		raise NotImplementedError("The execute method of the BaseTest class must be implemented in a subclass")


	def validate(self):
		"""Validate method which may optionally be overridden to group all validation steps.
		
		"""
		pass


	def cleanup(self):
		"""Cleanup method which performs cleanup actions after execution and validation of the test.
		
		The cleanup method performs actions to stop all processes started in the background and not 
		explicitly killed during the test execution. It also stops all process monitors running in 
		separate threads, and any instances of the manual tester user interface.
		
		Should a custom cleanup for a subclass be required, use L{addCleanupFunction} instead of overriding
		this method.
				
		"""
		try:
			if self.manualTester and self.manualTester.running():
				self.stopManualTester()

			# first request them all to stop
			# although we don't yet state this method is thread-safe, make it 
			# as thread-safe as possible by using swap operations
			with self.lock:
				threads, self.__backgroundThreads = list(self.__backgroundThreads), []
			for th in threads: th.stop()
			for th in threads: th.join(abortOnError=False)
		
			for monitor in self.monitorList:
				if monitor.running(): monitor.stop()
	
			while len(self.resources) > 0:
				self.resources.pop()
		finally:
			ProcessUser.cleanup(self)


	def addResource(self, resource):
		"""Add a resource which is owned by the test and is therefore
		cleaned up (deleted) when the test is cleaned up. 
		
		Deprecated - please use addCleanupFunction instead of this function. 
		"""
		self.resources.append(resource)


	def startProcessMonitor(self, process, interval=5, file=None, handlers=[], **pmargs):
		"""Start a background thread to monitor process statistics such as memory and CPU usage.
		
		All process monitors are automatically stopped on completion of 
		the test by L{BaseTest.cleanup}, but you may also wish to explicitly stop 
		your process monitors using L{stopProcessMonitor} before you begin 
		shutting down processes at the end of a test to avoid unwanted spikes 
		and noise in the last few samples of the data. 
		
		You can specify a `file` and/or a list of `handlers`. If you use 
		`file`, a default L{pysys.process.monitor.ProcessMonitorTextFileHandler} 
		instance is created to produce tab-delimited lines with default columns 
		specified by 
		L{pysys.process.monitor.ProcessMonitorTextFileHandler.DEFAULT_COLUMNS}. 
		If you wish to customize this for an individual test create your own 
		C{ProcessMonitorTextFileHandler} instance and pass it to handlers instead. 
		Additional default columns may be added in future releases. 
		
		@param process: The process handle returned from the L{startProcess} method.
		
		@param interval: The polling interval in seconds between collection of 
		monitoring statistics. 
		
		@param file: The name of a tab separated values (.tsv) file to write to, 
		for example 'monitor-myprocess.tsv'. 
		A default L{pysys.process.monitor.ProcessMonitorTextFileHandler} instance is 
		created if this parameter is specified, with default columns from 
		L{pysys.process.monitor.ProcessMonitorTextFileHandler.DEFAULT_COLUMNS} . 
		
		@param handlers: A list of L{pysys.process.monitor.BaseProcessMonitorHandler} 
		instances (such as L{pysys.process.monitor.ProcessMonitorTextFileHandler}), 
		which will process monitoring data every polling interval. This can be 
		used for recording results (for example in a file) or for dynamically 
		analysing them and reporting problems. 
		
		@param pmargs: Keyword arguments to allow advanced parameterization 
		of the process monitor class, which will be passed to its 
		constructor. It is an error to specify any parameters 
		not supported by the process monitor class on each platform. 
				
		@return: An object representing the process monitor 
		(L{pysys.process.monitor.BaseProcessMonitor}).
		@rtype: pysys.process.monitor.BaseProcessMonitor
		
		"""
		if isstring(file): file = os.path.join(self.output, file)
		handlers = [] if handlers is None else list(handlers)
		if file:
			handlers.append(ProcessMonitorTextFileHandler(file))
		
		self.log.debug("Starting process monitor for %r", process)
		monitor = DEFAULT_PROCESS_MONITOR(owner=self, process=process, interval=interval, handlers=handlers, **pmargs).start()
		assert hasattr(monitor, '_getData'), 'Start did not return a process monitor instance'
		self.monitorList.append(monitor)
		return monitor

	
	def stopProcessMonitor(self, monitor):
		"""Request a process monitor to stop.
		
		Does not wait for it to finish stopping. 

		All process monitors are automatically stopped and joined during cleanup, 
		however you may wish to explicitly stop your process monitors 
		before you begin shutting down processes at the end of a test to avoid 
		unwanted spikes and noise in the last few samples of the data. 
		
		@param monitor: The process monitor handle returned from the L{startProcessMonitor} method
		
		"""
		monitor.stop()

	def startBackgroundThread(self, name, target, kwargsForTarget={}):
		"""
		Start a new background thread that will invoke the specified `target` 
		function. 
		
		The target function will be invoked with the specified keyword 
		arguments and also the special keyword argument `stopping` which is 
		a Python C{threading.Event} instance that can be used to detect 
		when the thread has been requested to terminate. It is recommended 
		to use this event instead of C{time.sleep} to avoid waiting when 
		the thread is meant to be finishing. 
		
		Example usage::
			class PySysTest(BaseTest):
				def dosomething(self, stopping, log, param1, pollingInterval):
					log.debug('Message from my thread')
					while not stopping.is_set():
		
						# ... do stuff here
		
						# sleep for pollingInterval, waking up if requested to stop; 
						# (hint: ensure this wait time is small to retain 
						# responsiveness to Ctrl+C interrupts)
						if stopping.wait(pollingInterval): return
		
				def execute(self):
					t = self.startBackgroundThread('DoSomething1', self.dosomething, {'param1':True, 'pollingInterval':1.0})
					...
					t.stop() # requests thread to stop but doesn't wait for it to stop
					t.join()
		
		Note that C{BaseTest} is not thread-safe (apart from C{addOutcome}, 
		C{startProcess} and the reading of fields like self.output that don't 
		change) so if you need to use its fields or methods from 
		background threads, be sure to add your own locking to the foreground 
		and background threads in your test, including any custom cleanup 
		functions. 
		
		The BaseTest will stop and join all running background threads at the 
		beginning of cleanup. If a thread doesn't stop within the expected 
		timeout period a L{constants.TIMEDOUT} outcome will be appended. 
		If a thread's `target` function raises an Exception then a 
		L{constants.BLOCKED} outcome will be appended during cleanup or 
		when it is joined. 
		
		@param name: A name for this thread that concisely describes its purpose. 
		Should be unique within this test/owner instance. 
		A prefix indicating the test/owner will be added to the provided name. 
		
		@param target: The function or instance method that will be executed 
		on the background thread. The function must accept a keyword argument 
		named `stopping` in addition to whichever keyword arguments are 
		specified in `kwargsForTarget`. 
		
		@param kwargsForTarget: A dictionary of keyword arguments that will be 
		passed to the target function. 
		
		@return: A L{pysys.utils.threadutils.BackgroundThread} instance 
		wrapping the newly started thread. 
		@rtype: L{pysys.utils.threadutils.BackgroundThread}
		
		"""
		t = BackgroundThread(self, name=name, target=target, kwargsForTarget=kwargsForTarget)
		t.thread.start()
		with self.lock:
			self.__backgroundThreads.append(t)
		return t

	# methods to control the manual tester user interface
	def startManualTester(self, file, filedir=None, state=FOREGROUND, timeout=TIMEOUTS['ManualTester']): # pragma: no cover
		"""Start the manual tester.
		
		The manual tester user interface (UI) is used to describe a series of manual steps to be performed 
		to execute and validate a test. Only a single instance of the UI can be running at any given time, and 
		can be run either in the C{FOREGROUND} (method will not return until the UI is closed or the timeout
		occurs) or in the C{BACKGROUND} (method will return straight away so automated actions may be performed 
		concurrently). Should the UI be terminated due to expiry of the timeout, a C{TIMEDOUT} outcome will be 
		added to the outcome list. The UI can be stopped via the L{stopManualTester} method. An instance of the 
		UI not explicitly stopped within a test will automatically be stopped via the L{cleanup} method of the 
		BaseTest.
		
		@param file: The name of the manual test xml input file (see L{pysys.xml.manual} for details on the DTD)
		@param filedir: The directory containing the manual test xml input file (defaults to the output subdirectory)
		@param state: Start the manual tester either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate a manual tester running in the C{FOREGROUND}
		
		"""
		if filedir is None: filedir = self.input
	
		if not self.manualTester or self.manualTester.running() == 0:
			self.manualTester = ManualTester(self, os.path.join(filedir, file))
			t = threading.Thread(target=self.manualTester.start, name=self.__class__.__name__+'.manualtester')
			t.start()
		
			if state == FOREGROUND:
				startTime = time.time()
				while self.manualTester.running() == 1:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						self.addOutcome(TIMEDOUT, 'Manual tester timed out')
						self.manualTester.stop()
						return
					time.sleep(1)
			else:
				time.sleep(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester failed')


	def stopManualTester(self):  # pragma: no cover
		"""Stop the manual tester if running.
		
		"""
		if self.manualTester and self.manualTester.running():
			self.manualTester.stop()
			time.sleep(1)
		else:
			self.addOutcome(BLOCKED, 'Manual tester could not be stopped')


	def waitManualTester(self, timeout=TIMEOUTS['ManualTester']):  # pragma: no cover
		"""Wait for the manual tester to be stopped via user interaction.
		
		"""
		if self.manualTester and self.manualTester.running():
			startTime = time.time()
			while self.manualTester.running() == 1:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					self.addOutcome(TIMEDOUT, 'Timed out waiting for manual tester')
					self.manualTester.stop()
					return
				time.sleep(1)


	# test timing methods. These allow control flow of the test to be set
	# on various conditions i.e. a socket becoming available for connections,
	# a file to exist etc
	def wait(self, interval):
		"""Wait for a specified period of time.
		
		@param interval: The time interval in seconds to wait
		
		"""
		log.info('Waiting for %0.1f seconds'%interval)
		time.sleep(interval)


	# test validation methods.
	
	def assertPathExists(self, path, exists=True, abortOnError=False):
		"""Perform a validation that the specified file or directory path exists 
		(or does not exist). 
		
		@param path: The path to be checked. This can be an absolute path or 
		relative to the testcase output directory.

		@param exists: True if the path is asserted to exist, False if it 
		should not. 
		
		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 
		
		"""
		self.addOutcome(PASSED if pathexists(os.path.join(self.output, path))==exists else FAILED, 
			'Assertion that path exists=%s for "%s"'%(exists, os.path.normpath(path)), 
			abortOnError=abortOnError)

	def assertEval(self, evalstring, abortOnError=False, **formatparams):
		"""Perform a validation based on substituting values into 
		a .format() string with named {} placeholders and then evaluating it with eval. 
		
		Example use::
		
			self.assertEval('os.path.size({filename}) > {origFileSize}', 	
				filename=self.output+'/file.txt', origFileSize=1000)
		
		See also L{getExprFromFile} which is often used to extract a piece of 
		data from a log file which can then be checked using this method. 
		
		@param evalstring: a string that will be formatted using .format(...) 
			with the specified parameters, and result in failure outcome if not true. 
			
			Parameters should be specified using {name} syntax, and quoting is not 
			required as string values are automatically escaped using repr. 
			e.g. 'os.path.size({filename}) > {origFileSize}'. 
			
			Do not use an f-string instead of explicitly passing formatparams, as 
			with an f-string this method will not know the names of the substituted 
			parameters which makes the intention of the assertion harder to 
			understand from looking at the test output. 
		
		@param formatparams: Named parameters for the format string, which 
			can be of any type. Use descriptive names for the parameters to produce 
			an assertion message that makes it really clear what is being checked. 
			
			String parameters will be automatically passed through `repr()` before 
			being formatted, so there is no need to perform additional 
			quoting or escaping of strings. 
		
		@param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. Unless abortOnError=True this method only throws 
			an exception if the format string is invalid; failure to execute the 
			eval(...) results in a BLOCKED outcome but no exception. 
		
		"""
		formatparams = {k: (repr(v) if isstring(v) else v) for (k,v) in formatparams.items()}
		toeval = evalstring.format(**formatparams)
		
		display = 'with: %s'%', '.join(['%s=%s'%(k, 
			# avoid excessively long messages by removing self.output (slightly complicated by the fact we called repr recently above)
			str(formatparams[k]).replace(self.output.replace('\\','\\\\'), '<outputdir>') 
			) for k in sorted(formatparams.keys())])
		
		try:
			result = bool(eval(toeval))
		except Exception as e:
			self.addOutcome(BLOCKED, 'Failed to evaluate "%s" due to %s - %s'%(toeval, e.__class__.__name__, e), abortOnError=abortOnError)
			return False
		
		if result:
			self.addOutcome(PASSED, 'Assertion %s passed %s'%(evalstring, display))
			return True
		else:
			self.addOutcome(FAILED, 'Assertion %s failed %s'%(evalstring, display), abortOnError=abortOnError)
			return False
			
	def assertThat(self, conditionstring, *args, **kwargs):
		"""[DEPRECATED] Perform a validation based on substituting values into 
		an old-style % format string and then evaluating it with eval. 
		
		This method is deprecated in favour of L{assertEval} which produces 
		more useful assertion failure messages and automatic quoting of strings. 

		The eval string should be specified as a format string, with zero or more %s-style
		arguments. This provides an easy way to check conditions that also produces clear
		outcome messages.
		
		The safest way to pass arbitrary arguments of type string is to use the 
		repr() function to add appropriate quotes and escaping. 

		e.g. self.assertThat('%d >= 5 or %s=="foobar"', myvalue, repr(mystringvalue))
		
		@deprecated: Use L{assertEval} instead. 
		
		@param conditionstring: A string will have any following args 
		substituted into it and then be evaluated as a boolean python 
		expression. 
		
		@param args: Zero or more arguments to be substituted into the format 
		string
		
		@keyword abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 

		@keyword assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		"""
		abortOnError = kwargs.pop('abortOnError',False)
		assertMessage = kwargs.pop('assertMessage',None)
		assert not kwargs, 'Invalid keyword arguments: %s'%kwargs.keys()
		try:
			expr = conditionstring
			if args:
				expr = expr % args
			
			result = bool(eval(expr))
		except Exception as e:
			self.addOutcome(BLOCKED, 'Failed to evaluate "%s" with args %r: %s'%(conditionstring, args, e), abortOnError=abortOnError)
			return
		
		if result:
			self.addOutcome(PASSED, assertMessage or ('Assertion on %s'%expr))
		else:
			self.addOutcome(FAILED, assertMessage or ('Assertion on %s'%expr), abortOnError=abortOnError)

	def assertTrue(self, expr, abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the supplied expression evaluating to true.
		
		Consider using L{assertEval} instead of this method, which produces 
		clearer assertion failure messages. 
		
		If the supplied expression evaluates to true a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to false, a C{FAILED} outcome is added.
		
		@param expr: The expression, as a boolean, to check for the True | False value
		
		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 
		
		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		"""
		msg = assertMessage or 'Assertion on boolean expression equal to true'
		if expr == True:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg, abortOnError=abortOnError)
	

	def assertFalse(self, expr, abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the supplied expression evaluating to false.
		
		Consider using L{assertEval} instead of this method, which produces 
		clearer assertion failure messages. 
		
		If the supplied expression evaluates to false a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to true, a C{FAILED} outcome is added.
		
		@param expr: The expression to check for the true | false value
		
		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 	
		
		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		"""
		msg = assertMessage or 'Assertion on boolean expression equal to false'
		if expr == False:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg, abortOnError=abortOnError)


	def assertDiff(self, file1, file2, filedir1=None, filedir2=None, ignores=[], sort=False, replace=[], includes=[], encoding=None, 
			abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the comparison of two input text files.
		
		This method performs a file comparison on two input files. The files are pre-processed prior to the 
		comparison to either ignore particular lines, sort their constituent lines, replace matches to regular 
		expressions in a line with an alternate value, or to only include particular lines. Should the files 
		after pre-processing be equivalent a C{PASSED} outcome is added to the test outcome list, otherwise
		a C{FAILED} outcome is added.
		
		Although this method can perform transformation of the files directly, it is often easier to instead use 
		L{copy} to perform the transformation (e.g. stripping out timestamps, finding lines of interest etc)
		and then separately call assertDiff on the processed file. This makes it easier to generate a suitable 
		reference file and to diagnose test failures. 
		
		@param file1: The basename of the first file used in the file comparison
		@param file2: The basename of the second file used in the file comparison (often a reference file)
		@param filedir1: The dirname of the first file (defaults to the testcase output subdirectory)
		@param filedir2: The dirname of the second file (defaults to the testcase reference directory)
		@param ignores: A list of regular expressions used to denote lines in the files which should be ignored
		@param sort: Boolean flag to indicate if the lines in the files should be sorted prior to the comparison
		@param replace: List of tuples of the form ('regexpr', 'replacement'). For each regular expression in the 
			list, any occurences in the files is replaced with the replacement value prior to the comparison being 
			carried out. This is often useful to replace timestamps in logfiles etc.
		@param includes: A list of regular expressions used to denote lines in the files which should be used in the 
			comparison. Only lines which match an expression in the list are used for the comparison
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 
		
		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 
		
		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		"""
		if filedir1 is None: filedir1 = self.output
		if filedir2 is None: filedir2 = self.reference
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		log.debug("Performing file comparison diff with file1=%s and file2=%s", f1, f2)
		
		msg = assertMessage or ('File comparison between %s and %s'%(file1, file2))
		unifiedDiffOutput=os.path.join(self.output, os.path.basename(f1)+'.diff')
		result = False
		try:
			result = filediff(f1, f2, 
				ignores, sort, replace, includes, unifiedDiffOutput=unifiedDiffOutput, encoding=encoding or self.getDefaultFileEncoding(f1))
		except Exception:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			try:
				self.addOutcome(PASSED if result else FAILED, msg, abortOnError=abortOnError)
			finally:
				if not result:
					self.logFileContents(unifiedDiffOutput, encoding=encoding or self.getDefaultFileEncoding(f1))


	def assertGrep(self, file, filedir=None, expr='', contains=True, ignores=None, literal=False, encoding=None, 
			abortOnError=False, assertMessage=None):
		"""Perform a validation assert on a regular expression occurring in a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		
		@param expr: The regular expression to check for in the file (or a string literal if literal=True), 
			for example " ERROR .*".
			
			For contains=False matches, you should end the expr with `.*` if you wish to include just the 
			matching text in the outcome failure reason. If contains=False and expr does not end with a `*` 
			then the entire matching line will be included in the outcome failure reason. 
			
			For contains=True matches, the expr itself is used as the outcome failure reason. 
		
		@param contains: Boolean flag to specify if the expression should or should not be seen in the file.
		
		@param ignores: Optional list of regular expressions that will be 
			ignored when reading the file. 
		
		@param literal: By default expr is treated as a regex, but set this to True to pass in 
		a string literal instead.
		
		@param encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		
		@param abortOnError: Set to True to make the test immediately abort if the
			assertion fails. 
		
		@param assertMessage: Overrides the string used to describe this 
			assertion in log messages and the outcome reason. 
		
		"""
		assert expr, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		if literal:
			def escapeRegex(expr):
				# use our own escaping as re.escape makes the string unreadable
				regex = expr
				expr = ''
				for c in regex:
					if c in '\\{}[]+?^$':
						expr += '\\'+c
					elif c in '().*/':
						expr += '['+c+']' # more readable
					else:
						expr += c
				return expr
			expr = escapeRegex(expr)

		log.debug("Performing %s contains=%s grep on file: %s", 'regex' if not literal else 'literal/non-regex', contains, f)
		try:
			result = filegrep(f, expr, ignores=ignores, returnMatch=True, encoding=encoding or self.getDefaultFileEncoding(f))
		except Exception:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			msg = assertMessage or ('Grep on %s %s %s'%(file, 'contains' if contains else 'does not contain', quotestring(expr) ))
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			# short message if it succeeded, more verbose one if it failed to help you understand why, 
			# including the expression it found that should not have been there
			outcome = PASSED if (result!=None) == contains else FAILED
			if outcome == PASSED: 
				if contains: log.debug('Grep on input file %s successfully matched expression %s with line: %s', 
					file, quotestring(expr), quotestring(result.string))
				msg = assertMessage or ('Grep on input file %s' % file)
			else:
			
				if assertMessage:
					msg = assertMessage
				elif contains:
					msg = 'Grep on %s contains %s'%(file, quotestring(expr))
				else:
					msg = 'Grep on %s does not contain %s failed with: %s'%(file, 
						quotestring(expr),
						# heuristic to give best possible message; expressions ending with .* are usually 
						# complete and help to remove timestamps etc from the start so best to return match only; if user didn't do 
						# that they probably haven't thought much about it and returning the entire match string 
						# is more useful (though strip off trailing newlines):
						quotestring(
							(result.group(0) if expr.endswith('*') else result.string).rstrip('\n\r')
							))
			self.addOutcome(outcome, msg, abortOnError=abortOnError)
		

	def assertLastGrep(self, file, filedir=None, expr='', contains=True, ignores=[], includes=[], encoding=None, 
			abortOnError=False, assertMessage=None):
		"""Perform a validation assert on a regular expression occurring in the last line of a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to check for in the last line of the file
		@param contains: Boolean flag to denote if the expression should or should not be seen in the file
		@param ignores: A list of regular expressions used to denote lines in the file which should be ignored
		@param includes: A list of regular expressions used to denote lines in the file which should be used in the assertion.#
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 

		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 

		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 				
		"""
		assert expr, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		log.debug("Performing contains=%s grep on last line of file: %s", contains, f)

		msg = assertMessage or ('Grep on last line of %s %s %s'%(file, 'contains' if contains else 'not contains', quotestring(expr)))
		try:
			result = lastgrep(f, expr, ignores, includes, encoding=encoding or self.getDefaultFileEncoding(f)) == contains
		except Exception:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			if result: msg = assertMessage or ('Grep on input file %s' % file)
			self.addOutcome(PASSED if result else FAILED, msg, abortOnError=abortOnError)


	def assertOrderedGrep(self, file, filedir=None, exprList=[], contains=True, encoding=None, 
			abortOnError=False, assertMessage=None):   
		"""Perform a validation assert on a list of regular expressions occurring in specified order in a text file.
		
		When the C{contains} input argument is set to true, this method will append a C{PASSED} outcome 
		to the test outcome list if the supplied regular expressions in the C{exprList} are seen in the file
		in the order they appear in the list; otherwise a C{FAILED} outcome is added. Should C{contains} be set 
		to false, a C{PASSED} outcome will only be added should the regular expressions not be seen in the file in 
		the order they appear in the list.
		
		@param file: The basename of the file used in the ordered grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param exprList: A list of regular expressions which should occur in the file in the order they appear in the list
		@param contains: Boolean flag to denote if the expressions should or should not be seen in the file in the order specified
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 

		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 

		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		
		"""
		assert exprList, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
	
		log.debug("Performing contains=%s ordered grep on %s for %s", contains, f, exprList)
		
		msg = assertMessage or ('Ordered grep on input file %s' % file)
		expr = None
		try:
			expr = orderedgrep(f, exprList, encoding=encoding or self.getDefaultFileEncoding(f))
		except Exception:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			if expr is None and contains:
				result = PASSED
			elif expr is None and not contains:
				result = FAILED
			elif expr is not None and not contains:
				result = PASSED
			else:
				result = FAILED

			if result == FAILED and expr: 
				msg += ' failed on expression \"%s\"'% expr
			self.addOutcome(result, msg, abortOnError=abortOnError)

	
	def assertLineCount(self, file, filedir=None, expr='', condition=">=1", ignores=None, encoding=None, 
			abortOnError=False, assertMessage=None):
		"""Perform a validation assert on the number of lines in a text file matching a specific regular expression.
		
		This method will add a C{PASSED} outcome to the outcome list if the number of lines in the 
		input file matching the specified regular expression evaluate to true when evaluated against 
		the supplied condition.
		
		@param file: The basename of the file used in the line count
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression string used to match a line of the input file
		@param condition: The condition to be met for the number of lines matching the regular expression
		@param ignores: A list of regular expressions that will cause lines to be excluded from the count
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 

		@param abortOnError: Set to True to make the test immediately abort if the
		assertion fails. 
		
		@param assertMessage: Overrides the string used to describe this 
		assertion in log messages and the outcome reason. 
		"""	
		assert expr, 'expr= argument must be specified'
		
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			numberLines = linecount(f, expr, ignores=ignores, encoding=encoding or self.getDefaultFileEncoding(f))
			log.debug("Number of matching lines in %s is %d", f, numberLines)
		except Exception:
			log.warn("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			msg = assertMessage or ('Line count on %s for %s%s '%(file, quotestring(expr), condition))
			self.addOutcome(BLOCKED, '%s failed due to %s: %s'%(msg, sys.exc_info()[0], sys.exc_info()[1]), abortOnError=abortOnError)
		else:
			if (eval("%d %s" % (numberLines, condition))):
				msg = assertMessage or ('Line count on input file %s' % file)
				self.addOutcome(PASSED, msg)
			else:
				msg = assertMessage or ('Line count on %s for %s%s (actual =%d) '%(file, quotestring(expr), condition, numberLines))
				self.addOutcome(FAILED, msg, abortOnError=abortOnError)

	def reportPerformanceResult(self, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		""" Reports a new performance result, with an associated unique key that identifies it for  comparison purposes.
		
		Where possible it is better to report the rate at which an operation can be performed (e.g. throughput)
		rather than the total time taken, since this allows the number of iterations to be increased .
		
		@param value: The value to be reported. Usually this is a float or integer, but string is 
		also permitted. 

		@param resultKey: A unique string that fully identifies what was measured, which will be
		used to compare results from different test runs. For example "HTTP transport message sending throughput
		using with 3 connections in SSL mode". The resultKey must be unique across all test cases and modes. It should be fully
		self-describing (without the need to look up extra information such as the associated testId). Do not include
		the test id or units in the resultKey string. It must be stable across different runs, so cannot contain
		process identifiers, date/times or other numbers that will vary. If possible resultKeys should be written
		so that related results will be together when all performance results are sorted by resultKey, which usually
		means putting general information near the start of the string and specifics (throughput/latency, sending/receiving)
		towards the end of the string. It should be as concise as possible (given the above).

		@param unit: Identifies the unit the the value is measured in, including whether bigger numbers are better or
		worse (used to determine improvement or regression). Must be an instance of L{pysys.utils.perfreporter.PerformanceUnit}.
		In most cases, use L{pysys.utils.perfreporter.PerformanceUnit.SECONDS} (e.g. for latency) or
		L{pysys.utils.perfreporter.PerformanceUnit.PER_SECOND} (e.g. for throughput); the string literals 's' and '/s' can be
		used as a shorthand for those PerformanceUnit instances.
		
		@param toleranceStdDevs: (optional) A float that indicates how many standard deviations away from the mean a
		result needs to be to be considered a regression.
		
		@param resultDetails: (optional) A dictionary of detailed information about this specific result 
		and/or test that should be recorded together with the result, for example detailed information about what mode 
		or versions the test is measuring. Note this is separate from the global run details shared across 
		all tests in this PySys execution, which can be customized by overriding 
		L{pysys.utils.perfreporter.CSVPerformanceReporter.getRunDetails}.

		"""
		for p in self.runner.performanceReporters:
			p.reportResult(self, value, resultKey, unit, toleranceStdDevs=toleranceStdDevs, resultDetails=resultDetails)
			
	def getDefaultFileEncoding(self, file, **xargs):
		"""
		Specifies what encoding should be used to read or write the specified 
		text file. The default implementation for BaseTest delegates to the 
		runner, which in turn gets its defaults from the pysyproject.xml 
		configuration. 
		
		See L{pysys.process.user.ProcessUser.getDefaultFileEncoding} for more details.
		"""
		return self.runner.getDefaultFileEncoding(file, **xargs)
	
	def pythonDocTest(self, pythonFile, pythonPath=None, output=None, environs=None, **kwargs):
		"""
		Execute the Python doctests that exist in the specified python file; 
		adds a FAILED outcome if any do not pass. 
		
		@param pythonFile: the absolute path to a python file name. 
		@param pythonPath: a list of directories to be added to the PYTHONPATH.
		@param output: the output file; if not specified, '%s-doctest.txt' is used with 
		the basename of the python file. 
		
		@param kwargs: extra arguments are passed to startProcess/startPython. 
		"""
		assert os.path.exists(os.path.abspath(pythonFile)), os.path.abspath(pythonFile)
		
		if not output: output = '%s-doctest.txt'%os.path.basename(pythonFile).replace('.py','')
		p = self.startPython(
			arguments=['-m', 'doctest', '-v', os.path.normpath(pythonFile)],
			environs=self.createEnvirons(overrides=[environs, {
				'PYTHONPATH':None if not pythonPath else os.pathsep.join(pythonPath or [])}]),
			stdout=output, 
			stderr=output+'.err', 
			displayName='Python doctest %s'%os.path.basename(pythonFile),
			ignoreExitStatus=True,
			abortOnError=False, 
			**kwargs
			)
		msg = 'Python doctest for %s'%(os.path.basename(pythonFile))
		try:
			msg += ': '+self.getExprFromFile(output, '\d+ passed.*\d+ failed') # appears whether it succeeds or fails
		except Exception: 
			msg += ': failed to execute correctly'
		try:
			msg += '; first failure is: '+self.getExprFromFile(output, '^File .*, line .*, in .*')
		except Exception:
			pass # probably it succeeded
		
		if p.exitStatus == 0:
			self.addOutcome(PASSED, msg)
		else:
			self.addOutcome(FAILED, msg)
			self.logFileContents(output+'.err') # in case there are any clues there
			
			# full doctest output is quite hard to read, so try to summarize just the failures 
			
			failures = []
			lines = [] # accumulate each test
			with openfile(os.path.join(self.output, output), encoding=locale.getpreferredencoding()) as f:
				for line in f:
					line = line.rstrip()
					if line=='Trying:': # start of a new one, end of previous one
						if lines and lines[-1]!='ok':
							failures.append(lines)
						lines = [line]
					elif line == 'ok': # ignore if passed; needed if last test was a pass
						lines = []
					else:
						lines.append(line)
				if lines and lines[-1]!='ok':
					failures.append(lines)
				
			for failure in failures:
				log.info('-'*20)
				for line in failure:
					log.warning('  %s'%line.rstrip())
				log.info('')
		
