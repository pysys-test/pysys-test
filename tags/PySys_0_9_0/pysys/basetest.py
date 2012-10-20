#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2012  M.B.Grieve

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
Contains the base test class for test execution and validation. 

For more information see the L{pysys.basetest.BaseTest} API documentation. 

"""
import sys, os, os.path, re, string, time, thread, logging, copy, math, stat

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filecopy import filecopy
from pysys.utils.filegrep import filegrep
from pysys.utils.filegrep import lastgrep
from pysys.utils.filediff import filediff
from pysys.utils.filegrep import orderedgrep
from pysys.utils.linecount import linecount
from pysys.process.user import ProcessUser
from pysys.process.helper import ProcessWrapper
from pysys.process.monitor import ProcessMonitor
from pysys.manual.ui import ManualTester
from pysys.process.user import ProcessUser


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
	
	Validation of the testcase is through the C{assert*} methods. Execution of each method appends an outcome
	to an internal data structure thus building up a record of the individual validation outcomes. Several 
	potential outcomes are supported by the PySys framework (C{SKIPPED}, C{BLOCKED}, C{DUMPEDCORE}, C{TIMEDOUT}, 
	C{FAILED}, C{NOTVERIFIED}, and C{PASSED}) and the overall outcome of the testcase is determined using a
	precedence order of the individual outcomes. All C{assert*} methods support variable argument lists for 
	common non-default parameters. Currently this only includes the C{assertMessage} parameter, to override the 
	default statement logged by the framework to stdout and the run log. 

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
		
	"""
	
	def __init__ (self, descriptor, outsubdir, runner):
		"""Create an instance of the BaseTest class.
		
		@param descriptor: The descriptor for the test giving all test details
		@param outsubdir: The output subdirectory the test output will be written to
		@param runner: Reference to the runner responsable for executing the testcase
		
		"""
		ProcessUser.__init__(self)
		self.descriptor = descriptor
		self.input = descriptor.input
		self.output = os.path.join(descriptor.output, outsubdir)
		self.reference = descriptor.reference
		self.runner = runner
		self.mode = runner.mode
		self.setKeywordArgs(runner.xargs)
		self.monitorList = []
		self.manualTester = None
		self.outcome = []
		self.log = log
		self.project = PROJECT


	def setKeywordArgs(self, xargs):
		"""Set the xargs as data attributes of the test class.
				
		Values in the xargs dictionary are set as data attributes using the builtin C{setattr} method. 
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
		sorted(list, key=lambda x: PRECEDENT.index(x))
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
		ProcessUser.__del__(self)
		
		if self.manualTester and self.manualTester.running():
			self.stopManualTester()
	
		for monitor in self.monitorList:
			if monitor.running(): monitor.stop()


	# process manipulation methods of ProcessUser
	def startProcess(self, command, arguments, environs=None, workingDir=None, state=FOREGROUND, timeout=None, stdout=None, stderr=None, displayName=None):
		"""Start a process running in the foreground or background, and return the process handle.

		The method allows spawning of new processes in a platform independent way. The command, arguments, environment and 
		working directory to run the process in can all be specified in the arguments to the method, along with the filenames
		used for capturing the stdout and stderr of the process. Processes may be started in the C{FOREGROUND}, in which case 
		the method does not return until the process has completed or a time out occurs, or in the C{BACKGROUND} in which case
		the method returns immediately to the caller returning a handle to the process to allow manipulation at a later stage. 
		All processes started in the C{BACKGROUND} and not explicitly killed using the returned process handle are automatically
		killed on completion of the test via the L{cleanup} method of the BaseTest. 

		This method uses the L{pysys.process.helper} module to start the process. On failure conditions the method may append 
		C{BLOCKED} or C{TIMEDOUT} outcomes to the test validation data structure when it was not possible to start the process 
		(e.g. command does not exist etc), or the timeout period expired (indicating a potential deadlock or livelock in the 
		process).
						
		@param command: The command to start the process (should include the full path)
		@param arguments: A list of arguments to pass to the command
		@param environs: A dictionary of the environment to run the process in (defaults to clean environment)
		@param workingDir: The working directory for the process to run in (defaults to the testcase output subdirectory)
		@param state: Run the process either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate processes running in the C{FOREGROUND}
		@param stdout: The filename used to capture the stdout of the process
		@param stderr: The filename user to capture the stderr of the process
		@param displayName: Logical name of the process used for display and reference counting (defaults to the basename of the command)
		@return: The process handle of the process (L{pysys.process.helper.ProcessWrapper})
		@rtype: handle

		"""
		if workingDir is None: workingDir = r'%s' % self.output
		if displayName is None: displayName = os.path.basename(command)
		if environs is None: environs = {}
		
		try:
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, stdout, stderr)
			process.start()
			if state == FOREGROUND:
				log.info("Executed %s in foreground with exit status = %d", displayName, process.exitStatus)
			elif state == BACKGROUND:
				log.info("Started %s in background with process id %d", displayName, process.pid)
		except ProcessError:
			log.warn("%s", sys.exc_info()[1], exc_info=0)
			self.addOutcome(BLOCKED)
		except ProcessTimeout:
			log.warn("Process timedout after %d seconds, stopping process", timeout)
			process.stop()
			self.addOutcome(TIMEDOUT)
		else:
			self.processList.append(process) 	
			try:
				if self.processCount.has_key(displayName):
					self.processCount[displayName] = self.processCount[displayName] + 1
				else:
			 		self.processCount[displayName] = 1
			except:
				pass
		return process


	def stopProcess(self, process):
		"""Send a soft or hard kill to a running process to stop its execution.
	
		This method uses the L{pysys.process.helper} module to stop a running process. 
		Should the request to stop the running process fail, a C{BLOCKED} outcome will 
		be added to the test outcome list.
		
		@param process: The process handle returned from the L{startProcess} method
		
		"""
		if process.running():
			try:
				process.stop()
				log.info("Stopped process with process id %d", process.pid)
			except ProcessError:
				log.warn("Unable to stop process")
				self.addOutcome(BLOCKED)


	def signalProcess(self, process, signal):
		"""Send a signal to a running process (Unix only).
	
		This method uses the L{pysys.process.helper} module to send a signal to a running 
		process. Should the request to send the signal to the running process fail, a 
		C{BLOCKED} outcome will be added to the test outcome list.
			
		@param process: The process handle returned from the L{startProcess} method
		@param signal: The integer value of the signal to send
		
		"""
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process with process id %d", signal, process.pid)
			except ProcessError:
				log.warn("Unable to send signal to process")
				self.addOutcome(BLOCKED)


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess} method
		@param timeout: The timeout value in seconds to wait before returning
		
		"""
		try:
			log.info("Waiting %d secs for process with process id %d", timeout, process.pid)
			process.wait(timeout)
		except ProcessTimeout:
			log.warn("Unable to wait for process")
			self.addOutcome(TIMEDOUT)


	def startProcessMonitor(self, process, interval, file, **kwargs):
		"""Start a separate thread to log process statistics to logfile, and return a handle to the process monitor.
		
		This method uses the L{pysys.process.monitor} module to perform logging of the process statistics, 
		starting the monitor as a seperate background thread. Should the request to log the statistics fail 
		a C{BLOCKED} outcome will be added to the test outcome list. All process monitors not explicitly 
		stopped using the returned handle are automatically stopped on completion of the test via the L{cleanup} 
		method of the BaseTest. 
		
		@param process: The process handle returned from the L{startProcess} method
		@param interval: The interval in seconds between collecting and logging the process statistics
		@param file: The full path to the filename used for logging the process statistics
		@param kwargs: Keyword arguments to allow platform specific configurations
				
		@return: A handle to the process monitor (L{pysys.process.monitor.ProcessMonitor})
		@rtype: handle
		
		"""
		monitor = ProcessMonitor(process.pid, interval, file, **kwargs)
		try:
			self.log.info("Starting process monitor on process with id = %d", process.pid)
			monitor.start()
		except ProcessError:
			self.log.warn("Unable to start process monitor")
			self.addOutcome(BLOCKED)
		else:
			self.monitorList.append(monitor)
			return monitor

	
	def stopProcessMonitor(self, monitor):
		"""Stop a process monitor.
		
		@param monitor: The process monitor handle returned from the L{startProcessMonitor} method
		
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


	# test validation methods. These methods provide means to validate the outcome of
	# a test based on the occurrence of regular expressions in text files. All methods
	# directly append to the test outcome list
	def assertTrue(self, expr, **xargs):
		"""Perform a validation assert on the supplied expression evaluating to true.
		
		If the supplied expression evaluates to true a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to false, a C{FAILED} outcome is added.
		
		@param expr: The expression, as a string, to check for the true | false value
		@param xargs: Variable argument list (see class description for supported parameters)
		
		"""
		if expr == True:
			self.addOutcome(PASSED)
			log.info('%s ... passed' % self.__assertMsg(xargs, 'Assertion on boolean expression equal to true'))
		else:
			self.addOutcome(FAILED)
			log.info('%s ... failed' % self.__assertMsg(xargs, 'Assertion on boolean expression equal to true'))
	

	def assertFalse(self, expr, **xargs):
		"""Perform a validation assert on the supplied expression evaluating to false.
		
		If the supplied expression evaluates to false a C{PASSED} outcome is added to the 
		outcome list. Should the expression evaluate to true, a C{FAILED} outcome is added.
		
		@param expr: The expression to check for the true | false value
		@param xargs: Variable argument list (see class description for supported parameters)
						
		"""
		if expr == False:
			self.addOutcome(PASSED)
			log.info('%s ... passed' % self.__assertMsg(xargs, 'Assertion on boolean expression equal to false'))
		else:
			self.addOutcome(FAILED)
			log.info('%s ... failed' % self.__assertMsg(xargs, 'Assertion on boolean expression equal to false'))


	def assertDiff(self, file1, file2, filedir1=None, filedir2=None, ignores=[], sort=False, replace=[], includes=[], **xargs):
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
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir1 is None: filedir1 = self.output
		if filedir2 is None: filedir2 = self.reference
		f1 = os.path.join(filedir1, file1)
		f2 = os.path.join(filedir2, file2)

		log.debug("Performing file comparison:")
		log.debug("  file1:       %s" % file1)
		log.debug("  filedir1:    %s" % filedir1)
		log.debug("  file2:       %s" % file2)
		log.debug("  filedir2:    %s" % filedir2)
		
		try:
			result = filediff(f1, f2, ignores, sort, replace, includes)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			logOutcome = log.info
			if result == True:
				result = PASSED
			else:
				result = FAILED
				logOutcome = log.warn
			self.outcome.append(result)
			logOutcome("%s ... %s", self.__assertMsg(xargs, 'File comparison between %s and %s' % (file1, file2)), LOOKUP[result].lower())


	def assertGrep(self, file, filedir=None, expr='', contains=True, **xargs):
		"""Perform a validation assert on a regular expression occurring in a text file.
		
		When the C{contains} input argument is set to true, this method will add a C{PASSED} outcome 
		to the test outcome list if the supplied regular expression is seen in the file; otherwise a 
		C{FAILED} outcome is added. Should C{contains} be set to false, a C{PASSED} outcome will only 
		be added should the regular expression not be seen in the file.
		
		@param file: The basename of the file used in the grep
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to check for in the file
		@param contains: Boolean flag to denote if the expression should or should not be seen in the file
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		log.debug("Performing grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		log.debug("  expr:       %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])
		
		try:
			result = filegrep(f, expr)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			logOutcome = log.info
			if result == contains:
				result = PASSED
			else:
				result = FAILED
				logOutcome = log.warn
			self.outcome.append(result)
			logOutcome("%s ... %s", self.__assertMsg(xargs, 'Grep on input file %s' % file), LOOKUP[result].lower())
			

	def assertLastGrep(self, file, filedir=None, expr='', contains=True, ignores=[], includes=[], **xargs):
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
		@param includes: A list of regular expressions used to denote lines in the file which should be used in the assertion.
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		log.debug("Performing grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		log.debug("  expr:       %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])
		
		try:
			result = lastgrep(f, expr, ignores, includes)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			logOutcome = log.info
			if result == contains:
				result = PASSED
			else:
				result = FAILED
				logOutcome = log.warn
			self.outcome.append(result)
			logOutcome("%s ... %s", self.__assertMsg(xargs, 'Grep on input file %s' % file), LOOKUP[result].lower())


	def assertOrderedGrep(self, file, filedir=None, exprList=[], contains=True, **xargs):   
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
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
	
		log.debug("Performing ordered grep on file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		for expr in exprList: log.debug("  exprList:   %s" % expr)
		log.debug("  contains:   %s" % LOOKUP[contains])
		
		try:
			expr = orderedgrep(f, exprList)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			logOutcome = log.info
			if expr is None and contains:
				result = PASSED
			elif expr is None and not contains:
				result = FAILED
				logOutcome = log.warn
			elif expr is not None and not contains:
				result = PASSED
			else:
				result = FAILED
				logOutcome = log.warn
			self.outcome.append(result)
			log.info('%s ... %s' % (self.__assertMsg(xargs, 'Ordered grep on input file %s' % file), LOOKUP[result].lower()))
			if result == FAILED: logOutcome("Ordered grep failed on expression \"%s\"", expr)


	def assertLineCount(self, file, filedir=None, expr='', condition=">=1", **xargs):
		"""Perform a validation assert on the number of lines in a text file matching a specific regular expression.
		
		This method will add a C{PASSED} outcome to the outcome list if the number of lines in the 
		input file matching the specified regular expression evaluate to true when evaluated against 
		the supplied condition.
		
		@param file: The basename of the file used in the line count
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression used to match a line of the input file
		@param condition: The condition to be met for the number of lines matching the regular expression
		@param xargs: Variable argument list (see class description for supported parameters)
				
		"""	
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)

		try:
			numberLines = linecount(f, expr)
			log.debug("Number of matching lines is %d"%numberLines)
		except IOError, value:
			self.addOutcome(BLOCKED)
		else:
			logOutcome = log.info
			if (eval("%d %s" % (numberLines, condition))):
				result = PASSED
				appender = ""
			else:
				result = FAILED
				appender = "[%d%s]" % (numberLines, condition)
				logOutcome = log.warn
			self.outcome.append(result)
			logOutcome("%s ... %s %s", self.__assertMsg(xargs, 'Line count on input file %s' % file), LOOKUP[result].lower(), appender)


	def __assertMsg(self, xargs, default):
		"""Return an assert statement requested to override the default value.
		
		@param xargs: Variable argument list to an assert method
		@param default: Default assert statement to return if a parameter is not supplied
		
		"""
		if xargs.has_key('assertMessage'): return xargs['assertMessage']
		return default
