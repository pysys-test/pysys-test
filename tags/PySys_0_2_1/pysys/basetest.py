#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

import sys, os, os.path, re, string, time, thread, logging, copy

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filecopy import filecopy
from pysys.utils.filegrep import filegrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.process.helper import ProcessWrapper
from pysys.process.monitor import ProcessMonitor
from pysys.manual.ui import ManualTester

log = logging.getLogger('pysys.test')
log.setLevel(logging.NOTSET)


TEST_TEMPLATE = '''%s
%s

class %s(%s):
	def execute(self):
		pass

	def validate(self):
		pass
'''


class BaseTest:
	"""The base class for all PySys test classes.

	BaseTest is the parent class of all PySys system tests, and should be subclassed to provide 
	an implementation of the L{execute()} method. Additional L{setup()}, L{cleanup()} and L{validate()}
	methods provide the ability to perform custom setup and cleanup actions for a particual test, and to 
	perform all validation steps in a single method should this prove logically more simple.
	
	The class provides utility functions for process management, test timing and test validation. 
	Validation of the test can be performed multiple times through the C{assert*} functions, building 
	up an internal data structure storing the individual validation outcomes. The overall outcome of 
	the test is determined using a precedence order of the individual outcomes. 
	"""

	def __init__ (self, descriptor, outsubdir, mode, xargs):
		"""Create an instance of the BaseTest class.
		
		@param descriptor: The descriptor for the test giving all test details
		@param outsubdir: The output subdirectory the test output will be written to
		@param mode: The user defined mode the test is to be run in
		@param xargs: The dictionary of additional arguments to be set as data attributes to the test class
		
		"""
		self.descriptor = descriptor
		self.input = descriptor.input
		self.output = os.path.join(descriptor.output, outsubdir)
		self.reference = descriptor.reference
		self.mode = mode
		self.setKeywordArgs(xargs)
		self.processList = []
		self.monitorList = []
		self.manualTester = None
		self.outcome = []
		self.log = log


	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the test class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr()} method. 
		Thus an xargs dictionary of the form C{{'foo': 'bar'}} will result in a data attribute of the 
		form C{self.foo} with C{value bar}. This is used so that subclasses can define default values of 
		data attributes, which can be overriden on instantiation e.g. using the -X options to the 
		runTest.py launch executable.
		
		@param xargs: A dictionary of the user defined extra arguments
		
		"""
		for key in xargs.keys():
			setattr(self, key, xargs[key])


	# methods to add to and obtain the test outcome
	def addOutcome(self, outcome):
		"""Add a test validation outcome to the validation list.
		
		The method provides the ability to add a validation outcome to the internal data structure 
		storing the list of test validation outcomes. In a single test run multiple validations may 
		be performed. The currently supported validation outcomes are::
				
		  SKIPPED:     An execution/validation step of the test was skipped (e.g. deliberately)
		  BLOCKED:     An execution/validation step of the test could not be run (e.g. a missing resource)
		  DUMPEDCORE:  A process started by the test produced a core file (unix only)
		  TIMEDOUT:    An execution/validation step of the test timed out (e.g. process deadlock)
		  FAILED:      A validation step of the test failed
		  NOTVERIFIED: No validation steps were performed
		  INSPECT:     A validation step of the test requires manual inspection
		  PASSED:      A validation step of the test passed 
		
		The outcomes are considered to have a precedence order, as defined by the order of the outcomes listed
		above. Thus a C{BLOCKED} outcome has a higher precedence than a C{PASSED} outcome. The outcomes are defined 
		in L{pysys.constants}. 
		
		@param outcome: The outcome to add
		
		"""
		self.outcome.append(outcome)


	def getOutcome(self):
		"""Get the overall outcome of the test based on the precedence order.
				
		The method returns the overal outcome of the test based on the outcomes stored in the internal data 
		structure. The precedence order of the possible outcomes is used to determined the overall outcome 
		of the test, e.g. if C{PASSED}, C{BLOCKED} and C{FAILED} were recorded during the execution of the test, 
		the overall outcome would be C{BLOCKED}. 
		
		The method returns the integer value of the outcome as defined in L{pysys.constants}. To convert this 
		to a string representation use the C{LOOKUP} dictionary i.e. C{LOOKUP}[test.getOutcome()]
		
		@return: The overall test outcome
		@rtype:  integer

		"""	
		if len(self.outcome) == 0: return NOTVERIFIED
		list = copy.copy(self.outcome)
		list.sort(lambda x, y: cmp(PRECEDENT.index(x), PRECEDENT.index(y)))
		return list[0]


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
		raise NotImplementedError, "The execute method of the BaseTest class must be implemented in a subclass"


	def validate(self):
		"""Validate method which may optionally be overridden to group all validation steps.
		
		"""
		pass


	def cleanup(self):
		"""Cleanup method which performs cleanup actions after execution and validation of the test.
		
		The cleanup method performs actions to stop all processes started in the background and not 
		explicitly killed during the test execution. It also stops all process monitors running in 
		seperate threads, and any instances of the manual tester user interface. Should a custom cleanup 
		for a subclass be required, the BaseTest cleanup method should first be called. e.g. ::
		
		  class MyTest(BaseTest):
		  
		    def cleanup(self):
		      # call base test cleanup first
		      BaseTest.cleanup(self)
				
		      # perform custom cleanup actions
		      ...
				
		"""
		if self.manualTester and self.manualTester.running():
			self.stopManualTester()
	
		for monitor in self.monitorList:
			if monitor.running(): monitor.stop()

		for process in self.processList:
			if process.running(): process.stop()


	# process manipulation methods
	def startProcess(self, command, arguments, environs={}, workingDir=None, state=FOREGROUND, timeout=None, stdout=None, stderr=None, displayName=None):
		"""Start a process running in the foreground or background, and return the exit status or process handle respectively.

		The method allows spawning of new processes in a platform independent way. The command, arguments, environment and 
		working directory to run the process in can all be specified in the arguments to the method, along with the filenames
		used for capturing the stdout and stderr of the process. Processes may be started in the C{FOREGROUND}, in which case 
		the method does not return until the process has completed or a time out occurs, or in the C{BACKGROUND} in which case
		the method returns immediately to the caller returning a handle to the process to allow manipulation at a later stage. 
		All processes started in the C{BACKGROUND} and not explicitly killed using the returned process handle are automatically
		killed on completion of the test via the L{cleanup()} method of the BaseTest. 

		This method uses the L{pysys.process.helper} module to start the process. On failure conditions the method may append 
		C{BLOCKED} or C{TIMEDOUT} outcomes to the test validation data structure when it was not possible to start the process 
		(e.g. command does not exist etc), or the timeout period expired (indicating a potential deadlock or livelock in the process).
						
		@param command: The command to start the process (should include the full path)
		@param arguments: A list of arguments to pass to the command
		@param environs: A dictionary of the environment to run the process in (defaults to clean environment)
		@param workingDir: The working directory for the process to run in (defaults to the testcase output subdirectory)
		@param state: Run the process either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate processes running in the C{FOREGROUND}
		@param stdout: The filename used to capture the stdout of the process
		@param stderr: The filename user to capture the stderr of the process
		@param displayName: A display name to use (defaults to the basename of the command)
		@return: The exit status of a C{FOREGROUND} process, or process handle of a C{BACKGROUND} process
		@rtype: integer | handle

		"""
		if workingDir == None: workingDir = r'%s' % self.output
		if displayName == None: displayName = os.path.basename(command)
		
		try:
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, stdout, stderr)
			process.start()
			if state == FOREGROUND:
				log.info("Executed %s in foreground with exit status = %d", displayName, process.exitStatus)
			elif state == BACKGROUND:
				log.info("Started %s in background with process id %d", displayName, process.pid)
		except ProcessError:
			log.info("Unable to start process")
			self.addOutcome(BLOCKED)
		except ProcessTimeout:
			log.info("Process timedout after %d seconds", timeout)
			self.addOutcome(TIMEDOUT)
		else:
			self.processList.append(process)
			return process

		
	def stopProcess(self, process, hard=TRUE):
		"""Send a soft or hard kill to a running process to stop it's execution.
	
		This method uses the L{pysys.process.helper} module to stop a running process. 
		Should the request to stop the running process fail, a C{BLOCKED} outcome will 
		be added to the test outcome list.
		
		@param process: The process handle returned from the L{startProcess()} method
		@param hard: Set to false to perform a soft kill on the process (Unix systems only)
		
		"""
		if process.running():
			try:
				process.stop(hard)
				log.info("Stopped process with process id %d", process.pid)
			except ProcessError:
				log.info("Unable to stop process")
				self.addOutcome(BLOCKED)


	def signalProcess(self, process, signal):
		"""Send a signal to a running process (Unix only).
	
		This method uses the L{pysys.process.helper} module to send a signal to a running 
		process. Should the request to send the signal to the running process fail, a 
		C{BLOCKED} outcome will be added to the test outcome list.
			
		@param process: The process handle returned from the L{startProcess()} method
		@param signal: The integer value of the signal to send
		
		"""
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process with process id %d", signal, process.pid)
			except ProcessError:
				log.info("Unable to send signal to process")
				self.addOutcome(BLOCKED)


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess()} method
		@param timeout: The timeout value in seconds to wait before returning
		
		@todo: The underlying implementation in the process helper needs to be implemented
		"""
		try:
			log.info("Waiting %d secs for process with process id %d", timeout, process.pid)
			process.waitProcess(timeout)
		except ProcessTimeout:
			log.info("Unable to wait for process")
			self.addOutcome(TIMEDOUT)


	def startProcessMonitor(self, process, interval, file):
		"""Start a separate thread to log process statistics to logfile, and return a handle to the process monitor.
		
		This method uses the L{pysys.process.monitor} module to perform logging of the process statistics, 
		starting the monitor as a seperate background thread. Should the request to log the statistics fail 
		a C{BLOCKED} outcome will be added to the test outcome list. All process monitors not explicitly 
		stopped using the returned handle are automatically stopped on completion of the test via the L{cleanup()} 
		method of the BaseTest. 
		
		@param process: The process handle returned from the L{startProcess()} method
		@param interval: The interval in seconds between collecting and logging the process statistics
		@param file: The full path to the filename used for logging the process statistics
		
		@return: A handle to the process monitor
		@rtype: handle
		
		"""
		monitor = ProcessMonitor(process, interval, file)
		try:
			monitor.start()
		except ProcessError:
			self.addOutcome(BLOCKED)
		else:
			self.monitorList.append(monitor)
			return monitor


	def stopProcessMonitor(self, monitor):
		"""Stop a process monitor.
		
		@param monitor: The process monitor handle returned from the L{startProcessMonitor()} method
		
		"""
		if monitor.running: monitor.stop()


	# methods to control the manual tester user interface
	def startManualTester(self, file, filedir=None, state=FOREGROUND, timeout=TIMEOUTS['ManualTester']):
		"""Start the manual tester.
		
		The manual tester user interface (UI) is used to describe a series of manual steps to be performed 
		to execute and validate a test. Only a single instance of the UI can be running at any given time, and 
		can be run either in the C{FOREGROUND} (method will not return until the UI is closed or the timeout
		occurs) or in the C{BACKGROUND} (method will return straight away so automated actions may be performed 
		concurrently). Should the UI be terminated due to expiry of the timeout, a C{TIMEDOUT} outcome will be 
		added to the outcome list. The UI can be stopped via the L{stopManualTester()} method. An instance of the 
		UI not explicitly stopped within a test will automatically be stopped via the L{cleanup()} method of the 
		BaseTest.
		
		@param file: The name of the manual test xml input file (see L{pysys.xml.manual} for details on the DTD)
		@param filedir: The directory containing the manual test xml input file (defaults to the output subdirectory)
		@param state: Start the manual tester either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate a manual tester running in the C{FOREGROUND}
		
		"""
		if filedir == None: filedir = self.input
	
		if not self.manualTester or self.manualTester.running() == 0:
			self.manualTester = ManualTester(self, os.path.join(filedir, file), os.path.join(self.output, 'manual.log'))
			thread.start_new_thread(self.manualTester.start, ())
		
			if state == FOREGROUND:
				startTime = time.time()
				while self.manualTester.running() == 1:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						self.addOutcome(TIMEDOUT)
						self.manualTester.stop()
						return
					time.sleep(1)
			else:
				time.sleep(1)
		else:
			self.addOutcome(BLOCKED)	


	def stopManualTester(self):
		"""Stop the manual tester if running.
		
		"""
		if self.manualTester and self.manualTester.running():
			self.manualTester.stop()
			time.sleep(1)
		else:
			self.addOutcome(BLOCKED)	


	def waitManualTester(self, timeout=TIMEOUTS['ManualTester']):
		"""Wait for the manual tester to be stopped via user interaction.
		
		"""
		if self.manualTester and self.manualTester.running():
			startTime = time.time()
			while self.manualTester.running() == 1:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					self.addOutcome(TIMEDOUT)
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
		time.sleep(interval)


	def waitForSocket(self, port, host='localhost', timeout=TIMEOUTS['WaitForSocket']):
		"""Wait for a socket connection to be established.
		
		This method blocks until connection to a particular host:port pair can be established. 
		This is useful for test timing where a component under test creates a socket for client 
		server interaction - calling of this method ensures that on return of the method call 
		the server process is running and a client is able to create connections to it. If a 
		connection cannot be made within the specified timeout interval, a C{TIMEDOUT} outcome 
		is written to the outcome list, and the method returns to the caller.
		
		@param port: The port value in the socket host:port pair
		@param host: The host value in the socket host:port pair
		@param timeout: The timeout in seconds to wait for connection to the socket
		
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		startTime = time.time()
		while 1:
			try:
				s.connect((host, port))
				break
			except socket.error:
				if timeout:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						break
			time.sleep(0.01)


	def waitForFile(self, filename, timeout=TIMEOUTS['WaitForFile']):
		"""Wait for a file to be written to disk.
		
		This method blocks until a file is created on disk. This is useful for test timing where 
		a component under test creates a file (e.g. for logging) indicating it has performed all 
		initialisation actions and is ready for the test execution steps. If a file is not created 
		on disk within the specified timeout interval, a C{TIMEDOUT} outcome is written to the outcome 
		list, and the method returns to the caller.
		
		@param filename: The full path to the file to wait for creation
		@param timeout: The timeout in seconds to wait for the file to be created
		
		"""
		startTime = time.time()
		while not os.path.exists(filename):
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					break
			time.sleep(0.01)


	def waitForSignal(self, basename, expr, condition=">=1", timeout=TIMEOUTS['WaitForSignal'], poll=0.25):
		"""Wait for a particular regular expression to be seen on a set number of lines in a text file.
		
		This method blocks until a particular regular expression is seen in a text file on a set
		number of lines. The number of lines which should match the regular expression is given by 
		the C{condition} argument in textual form i.e. for a match on more than 2 lines use condition =\">2\".
		If the regular expression is not seen in the file matching the supplied condition within the 
		specified timeout interval, a C{TIMEDOUT} outcome is written to the outcome list, and the method 
		returns to the caller.
		
		@param basename: The full path to the file to check for the regular expression
		@param exp: The regular expression to search for in the text file
		@param condition: The condition to be met for the number of lines matching the regular expression
		@param timeout: The timeout in seconds to wait for the regular expression and to check against the condition
		@param poll: The time in seconds to poll the file looking for the regular expression and to check against the condition
		"""
		file = os.path.join(self.output, basename)

		startTime = time.time()
		while 1:
			if os.path.exists(file):
				if eval("%d %s" % (linecount(file, expr), condition)):
					break
				
			currentTime = time.time()
			if currentTime > startTime + timeout:
				break
			time.sleep(poll)


	# test validation methods. These methods provide means to validate the outcome of
	# a test based on the occurrence of regular expressions in text files. All methods
	# directly append to the test outcome list
	def assertTrue(self, expr):
		"""Perform a validation assert on the supplied expression evaluating to true.
		
		If the supplied expression evaluates to true a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to false, a C{FAILED} outcome is added.
		
		@param expr: The expression to check for the true | false value
				
		"""
		if expr == TRUE:
			self.addOutcome(PASSED)
			log.info("Assertion on boolean expression equal to true ... passed")
		else:
			self.addOutcome(FAILED)
			log.info("Assertion on boolean expression equal to true ... failed")
	

	def assertFalse(self, expr):
		"""Perform a validation assert on the supplied expression evaluating to false.
		
		If the supplied expression evaluates to false a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to true, a C{FAILED} outcome is added.
		
		@param expr: The expression to check for the true | false value
				
		"""
		if expr == FALSE:
			self.addOutcome(PASSED)
			log.info("Assertion on boolean expression equal to true ... passed")
		else:
			self.addOutcome(FAILED)
			log.info("Assertion on boolean expression equal to true ... failed")
	

	def assertDiff(self, file1, file2, filedir1=None, filedir2=None, ignores=[], sort=FALSE, replace=[], includes=[]):
		"""Perform a validation assert on the comparison of two input text files.
		
		This method performs a file comparison on two input files. The files are pre-processed prior to the 
		comparison to either ignore particular lines, sort their constituent lines, replace matches to regular 
		expressions in a line with an alternate value, or to only include particular lines. Should the files 
		after pre-processing be equivalent a C{PASSED} outcome is added to the test outcome list, otherwise
		a C{FAILED} outcome is added.
		
		@param file1: The basename of the first file used in the file comparison
		@param file2: The basename of the second file used in the file comparison
		@param filedir1: The dirname of the first file (defaults to the testcase output subdirectory)
		@param filedir2: The dirname of the second file (defaults to the testcase reference directory)
		@param ignores: A list of regular expressions used to denote lines in the files which should be ignored
		@param sort: Boolean flag to indicate if the lines in the files should be sorted prior to the comparison
		@param replace: List of tuples of the form ('regexpr', 'replacement'). For each regular expression in the 
			list, any occurences in the files is replaced with the replacement value prior to the comparison being 
			carried out. This is often useful to replace timestamps in logfiles etc.
		@param includes: A list of regular expressions used to denote lines in the files which should be used in the 
			comparison. Only lines which match an expression in the list are used for the comparison
		
		"""
		if filedir1 == None: filedir1 = self.output
		if filedir2 == None: filedir2 = self.reference
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		try:
			result = filediff(f1, f2, ignores, sort, replace, includes)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == TRUE:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("File comparison between %s and %s ... %s", file1, file2, LOOKUP[result].lower())


	def assertGrep(self, file, filedir=None, expr='', contains=TRUE):
		"""Perform a validation assert on a regular expression occurring in a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to check for in the file
		@param contains: Boolean flag to denote if the expression should or should not be seen in the file
		
		"""
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			result = filegrep(f, expr)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == contains:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Grep on input file %s ... %s", file, LOOKUP[result].lower())


	def assertOrderedGrep(self, file, filedir=None, exprList=[], contains=TRUE):   
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
		
		"""
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			result = orderedgrep(f, exprList)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if result == None and contains:
				result = PASSED
			elif result == None and not contains:
				result = FAILED
			elif result != None and not contains:
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Ordered grep on input file %s ... %s", file, LOOKUP[result].lower())


	def assertLineCount(self, file, filedir=None, expr='', condition=">=1"):
		"""Perform a validation assert on the number of lines in a text file matching a specific regular expression.
		
		This method will add a C{PASSED} outcome to the outcome list if the number of lines in the 
		input file matching the specified regular expression evaluate to true when evaluated against 
		the supplied condition.
		
		@param file: The basename of the file used in the line count
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression used to match a line of the input file
		@param condition: The condition to be met for the number of lines matching the regular expression
		
		"""	
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			numberLines = linecount(f, expr)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			if (eval("%d %s" % (numberLines, condition))):
				result = PASSED
			else:
				result = FAILED
			self.outcome.append(result)
			log.info("Line count on input file %s ... %s", file, LOOKUP[result].lower())



	