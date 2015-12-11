#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2015  M.B.Grieve

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

import sys, os, time

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filegrep import getmatches
from pysys.process.helper import ProcessWrapper
from pysys.utils.allocport import TCPPortOwner


class ProcessUser(object):
	"""Class providing basic operations over interacting with processes.
	
	The ProcessUser class provides the mimimum set of operations for managing and interacting with 
	processes. The class is designed to be extended by the L{pysys.baserunner.BaseRunner} and 
	L{pysys.basetest.BaseTest} classes so that they prescribe a common set of process operations 
	that any application helper classes can use, i.e. where an application helper class is 
	instantiated with a callback reference to the runner or base test for the process operations. 
	
	This class has the ability to recored one or more 'outcomes', and many of 
	the methods on this class will append outcomes when errors occur, such as 
	an unsuccessful attempt to launch a process. Some subclasses may make 
	no use of the outcome, but it is used by BaseTest - see that class for 
	more details. 
	
	
	@ivar input: Location for input to any processes (defaults to current working directory) 
	@type input: string
	@ivar output: Location for output from any processes (defaults to current working directory)
	@type output: string

	"""
	
	def __init__(self):
		"""Default constructor.
		
		"""
		self.processList = []
		self.processCount = {}
		self.__cleanupFunctions = []

		self.outcome = [] # please use addOutcome instead of manipulating this directly
		self.__outcomeReason = ''


	def __getattr__(self, name):
		"""Set self.input or self.output to the current working directory if not defined.
		
		"""
		if name == "input" or name == "output":
			return os.getcwd()
		else:
			raise AttributeError("Unknown class attribute ", name)


	def getInstanceCount(self, displayName):
		"""Return the number of processes started within the testcase matching the supplied displayName.

		The ProcessUserInterface class maintains a reference count of processes started within the class instance 
		via the L{startProcess()} method. The reference count is maintained against a logical name for 
		the process, which is the displayName used in the method call to L{startProcess()}, or the 
		basename of the command if no displayName was supplied. The method returns the number of 
		processes started with the supplied logical name, or 0 if no processes have been started. 
		
		@param displayName: The process display name
		@return: The number of processes started matching the command basename
		@rtype:  integer
		
		"""
		if self.processCount.has_key(displayName):
			return self.processCount[displayName]
		else:
			return 0
		
	
	# process manipulation methods of ProcessUserInterface
	def startProcess(self, command, arguments, environs={}, workingDir=None, state=FOREGROUND, timeout=None, stdout=None, stderr=None, displayName=None):
		"""Start a process running in the foreground or background, and return the process handle.

		The method allows spawning of new processes in a platform independent way. The command, arguments, environment and 
		working directory to run the process in can all be specified in the arguments to the method, along with the filenames
		used for capturing the stdout and stderr of the process. Processes may be started in the C{FOREGROUND}, in which case 
		the method does not return until the process has completed or a time out occurs, or in the C{BACKGROUND} in which case
		the method returns immediately to the caller returning a handle to the process to allow manipulation at a later stage. 
		All processes started in the C{BACKGROUND} and not explicitly killed using the returned process handle are automatically
		killed on completion of the test via the L{cleanup()} destructor. 

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
		if not workingDir: workingDir = r'%s' % self.output
		if not displayName: displayName = os.path.basename(command)
		
		try:
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, stdout, stderr)
			process.start()
			if state == FOREGROUND:
				(log.info if process.exitStatus == 0 else log.warn)("Executed %s in foreground with exit status = %d", displayName, process.exitStatus)
			elif state == BACKGROUND:
				log.info("Started %s in background with process id %d", displayName, process.pid)
		except ProcessError, e:
			self.addOutcome(BLOCKED, '%s failed to run: %s'%(process, e))
		except ProcessTimeout:
			self.addOutcome(TIMEDOUT, '%s timed out after %d seconds'%(process, timeout), printReason=False)
			log.warn("Process timed out after %d seconds, stopping process", timeout)
			process.stop()
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
		be added to the outcome list.
		
		@param process: The process handle returned from the L{startProcess} method
		
		"""
		if process.running():
			try:
				process.stop()
				log.info("Stopped process with process id %d", process.pid)
			except ProcessError, e:
				self.addOutcome(BLOCKED, 'Unable to stop %s process: %s'%(process, e))


	def signalProcess(self, process, signal):
		"""Send a signal to a running process (Unix only).
	
		This method uses the L{pysys.process.helper} module to send a signal to a running 
		process. Should the request to send the signal to the running process fail, a 
		C{BLOCKED} outcome will be added to the outcome list.
			
		@param process: The process handle returned from the L{startProcess} method
		@param signal: The integer value of the signal to send
		
		"""
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process with process id %d", signal, process.pid)
			except ProcessError, e:
				self.addOutcome(BLOCKED, 'Unable to send signal to process %s: %s'%(process, e))


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess} method
		@param timeout: The timeout value in seconds to wait before returning
		
		"""
		try:
			log.info("Waiting %d secs for process %r", timeout, process)
			process.wait(timeout)
		except ProcessTimeout:
			self.addOutcome(TIMEDOUT, 'Timed out waiting for process %s after %d secs'%(process, timeout))


	def writeProcess(self, process, data, addNewLine=True):
		"""Write data to the stdin of a process.
		
		This method uses the L{pysys.process.helper} module to write a data string to the 
		stdin of a process. This wrapper around the write method of the process helper only 
		adds checking of the process running status prior to the write being performed, and 
		logging to the testcase run log to detail the write.
		
		@param process: The process handle returned from the L{startProcess()} method
		@param data: The data to write to the process		
		@param addNewLine: True if a new line character is to be added to the end of the data string
		
		"""
		if process.running():
			process.write(data, addNewLine)
			log.info("Written to stdin of process with process id %d", process.pid)
			log.debug("  %s" % data)
		else:
			log.info("Write to process with process id %d stdin not performed as process is not running", process.pid)


	def waitForSocket(self, port, host='localhost', timeout=TIMEOUTS['WaitForSocket']):
		"""Wait for a socket connection to be established.
		
		This method blocks until connection to a particular host:port pair can be established. 
		This is useful for test timing where a component under test creates a socket for client 
		server interaction - calling of this method ensures that on return of the method call 
		the server process is running and a client is able to create connections to it. If a 
		connection cannot be made within the specified timeout interval, the method returns 
		to the caller.
		
		@param port: The port value in the socket host:port pair
		@param host: The host value in the socket host:port pair
		@param timeout: The timeout in seconds to wait for connection to the socket
		
		"""
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		log.debug("Performing wait for socket creation:")
		log.debug("  file:       %d" % port)
		log.debug("  filedir:    %s" % host)
		
		exit = False
		startTime = time.time()
		while not exit:
			try:
				s.connect((host, port))
				exit = True
			except socket.error:
				if timeout:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						log.info("Timedout waiting for creation of socket")
						break
			time.sleep(0.01)
		if exit: log.debug("Wait for socket creation completed successfully")
	

	def waitForFile(self, file, filedir=None, timeout=TIMEOUTS['WaitForFile']):
		"""Wait for a file to be written to disk.
		
		This method blocks until a file is created on disk. This is useful for test timing where 
		a component under test creates a file (e.g. for logging) indicating it has performed all 
		initialisation actions and is ready for the test execution steps. If a file is not created 
		on disk within the specified timeout interval, the method returns to the caller.
		
		@param file: The basename of the file used to wait to be created
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param timeout: The timeout in seconds to wait for the file to be created
		
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
		
		log.debug("Performing wait for file creation:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		
		exit = False
		startTime = time.time()
		while not exit:
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					log.info("Timedout waiting for creation of file %s" % file)
					break
			time.sleep(0.01)
			exit = os.path.exists(f)
		if exit: log.debug("Wait for file creation completed successfully")

			
	def waitForSignal(self, file, filedir=None, expr="", condition=">=1", timeout=TIMEOUTS['WaitForSignal'], poll=0.25):
		"""Wait for a particular regular expression to be seen on a set number of lines in a text file.
		
		This method blocks until a particular regular expression is seen in a text file on a set
		number of lines. The number of lines which should match the regular expression is given by 
		the C{condition} argument in textual form i.e. for a match on more than 2 lines use condition =\">2\".
		If the regular expression is not seen in the file matching the supplied condition within the 
		specified timeout interval, the method returns to the caller.
		
		@param file: The basename of the file used to wait for the signal
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param expr: The regular expression to search for in the text file
		@param condition: The condition to be met for the number of lines matching the regular expression
		@param timeout: The timeout in seconds to wait for the regular expression and to check against the condition
		@param poll: The time in seconds to poll the file looking for the regular expression and to check against the condition
		"""
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
		
		log.debug("Performing wait for signal in file:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		log.debug("  expression: %s" % expr)
		log.debug("  condition:  %s" % condition)
		
		matches = []
		startTime = time.time()
		log.info("Wait for signal \"%s\" %s in %s", expr, condition, file)
		while 1:
			if os.path.exists(f):
				matches = getmatches(f, expr)
				if eval("%d %s" % (len(matches), condition)):
					log.info("Wait for signal in %s completed successfully", file)
					break
				
			currentTime = time.time()
			if currentTime > startTime + timeout:
				log.info("Wait for signal in %s timed out after %d secs", file, timeout)
				log.info("Number of matches to the expression are %d" % len(matches))
				break
			time.sleep(poll)
		return matches

	def addCleanupFunction(self, fn):
		""" Registers a zero-arg function that will be called as part of the 
		cleanup of this object, to provide a way to cleanly free associated 
		resources. 
		
		Cleanup functions are invoked in reverse order with the most recently 
		added first (LIFO), and before the automatic termination of any 
		remaining processes associated with this object.
		
		e.g. self.addCleanupFunction(lambda: self.cleanlyShutdownProcessX(params))
		
		"""
		if fn and fn not in self.__cleanupFunctions: 
			self.__cleanupFunctions.append(fn)

	def cleanup(self):
		""" Cleanup function that frees resources managed by this object. 
		Should be called exactly once when this object is no longer needed. 
		
		Instead of overriding this function, use L{addCleanupFunction}.  
		
		"""
		try:
			for fn in reversed(self.__cleanupFunctions):
				try:
					log.debug('Running registered cleanup function: %r'%fn)
					fn()
				except Exception, e:
					log.error('Error while running cleanup function: %s'%e)
			self.__cleanupFunctions = []
		finally:
			for process in self.processList:
				try:
					if process.running(): process.stop()
				except:
					 log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.processList = []
			self.processCount = {}
			
			log.debug('ProcessUser cleanup function done.')
		
	# methods to add to and obtain the outcome, used by BaseTest
	
	def addOutcome(self, outcome, outcomeReason='', printReason=True):
		"""Add a test validation outcome (and if possible, reason string) to the validation list.
		
		See also abort(), which should be used instead of this method for cases where 
		it doesn't make sense to continue running the test. 
		
		The method provides the ability to add a validation outcome to the internal data structure 
		storing the list of test validation outcomes. In a single test run multiple validations may 
		be performed. The currently supported validation outcomes are:
				
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
		@param outcomeReason: A string summarizing the reason for the outcome 
			to help anyone triaging test failures. 
			Callers are strongly recommended to specify this if at all possible 
			when reporting failure outcomes. 
			e.g. outcomeReason='Timed out running myprocess after 60 seconds'
		@param printReason: if True the specified outcomeReason will be printed 
			at INFO/WARN (whether or not this outcome reason is taking priority). 
			In most cases this is useful, but can be disabled if more specific 
			logging is already implemented. 
		
		"""
		assert outcome in PRECEDENT, outcome # ensure outcome type is known, and that numeric not string constant was specified! 
		outcomeReason = outcomeReason.strip() if outcomeReason else ''
		
		old = self.getOutcome()
		self.outcome.append(outcome)
		if self.getOutcome() != old:
			self.__outcomeReason = outcomeReason

		if outcomeReason and printReason:
			if outcome in FAILS:
				log.warn('Adding outcome %s: %s', LOOKUP[outcome], outcomeReason)
			else:
				log.info('Adding outcome %s: %s', LOOKUP[outcome], outcomeReason)

	def abort(self, outcome, outcomeReason):
		"""Immediately terminate execution of the current test (both execute and validate) 
		and report the specified outcome and outcomeReason string. 
		
		This method works by raising an AbortExecution exeception, so 
		do not add a try...except block around the abort call unless that is 
		really what is intended. 
		
		See addOutcome for the list of permissible outcome values. 
		
		@param outcome: The outcome, which will override any existing 
			outcomes previously reported. The most common outcomes are 
			BLOCKED, TIMEDOUT or SKIPPED. 
		@param outcomeReason: A string summarizing the reason for the outcome 
			to help anyone triaging test failures. 
			e.g. outcomeReason='Timed out running myprocess after 60 seconds'
		
		"""	
		raise AbortExecution(outcome, outcomeReason)
	
	def getOutcome(self):
		"""Get the overall outcome of the test based on the precedence order.
				
		The method returns the overal outcome of the test based on the outcomes stored in the internal data 
		structure. The precedence order of the possible outcomes is used to determined the overall outcome 
		of the test, e.g. if C{PASSED}, C{BLOCKED} and C{FAILED} were recorded during the execution of the test, 
		the overall outcome would be C{BLOCKED}. 
		
		The method returns the integer value of the outcome as defined in L{pysys.constants}. To convert this 
		to a string representation use the C{LOOKUP} dictionary i.e. C{LOOKUP}[test.getOutcome()]
		
		@return: The overall outcome
		@rtype:  integer

		"""	
		if len(self.outcome) == 0: return NOTVERIFIED
		return sorted(self.outcome, key=lambda x: PRECEDENT.index(x))[0]
		
	def getOutcomeReason(self):
		"""Get the reason string for the current overall outcome (if specified).
				
		@return: The overall test outcome reason or '' if not specified
		@rtype:  string

		"""	
		return self.__outcomeReason

	def getNextAvailableTCPPort(self):
		"""Allocate a TCP port which is available for a server to be
		started on. Take ownership of it for the duration of the test
		"""
		o = TCPPortOwner()
		self.addCleanupFunction(lambda: o.cleanup())
		return o.port
