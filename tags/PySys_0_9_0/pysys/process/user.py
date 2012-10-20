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

import sys, os, time

from pysys import log
from pysys.constants import *
from pysys.utils.filegrep import getmatches
from pysys.process.helper import ProcessWrapper


class ProcessUser:
	"""Class providing basic operations over interacting with processes.
	
	The ProcessUser class provides the mimimum set of operations for managing and interacting with 
	processes. The class is designed to be extended by the L{pysys.baserunner.BaseRunner} and 
	L{pysys.basetest.BaseTest} classes so that they prescribe a common set of process operations 
	that any application helper classes can use, i.e. where an application helper class is 
	instantiated with a call back reference to the runner or base test for the process operations. 
	
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
		killed on completion of the test via the L{__del__()} destructor. 

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
		
		try:
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, stdout, stderr)
			process.start()
			if state == FOREGROUND:
				log.info("Executed %s in foreground with exit status = %d", displayName, process.exitStatus)
			elif state == BACKGROUND:
				log.info("Started %s in background with process id %d", displayName, process.pid)
		except ProcessError:
			log.info("%s", sys.exc_info()[1], exc_info=0)
		except ProcessTimeout:
			log.info("Process timedout after %d seconds, stopping process", timeout)
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
		
		@param process: The process handle returned from the L{startProcess()} method
		
		"""
		if process.running():
			try:
				process.stop()
				log.info("Stopped process with process id %d", process.pid)
			except ProcessError:
				log.info("Unable to stop process")


	def signalProcess(self, process, signal):
		"""Send a signal to a running process (Unix only).
	
		This method uses the L{pysys.process.helper} module to send a signal to a running 
		process. 
		
		@param process: The process handle returned from the L{startProcess()} method
		@param signal: The integer value of the signal to send
		
		"""
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process with process id %d", signal, process.pid)
			except ProcessError:
				log.info("Unable to send signal to process")


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess()} method
		@param timeout: The timeout value in seconds to wait before returning
		
		"""
		try:
			log.info("Waiting %d secs for process with process id %d", timeout, process.pid)
			process.wait(timeout)
		except ProcessTimeout:
			log.info("Unable to wait for process")


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
		connection cannot be made within the specified timeout interval, a C{TIMEDOUT} outcome 
		is written to the outcome list, and the method returns to the caller.
		
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
		on disk within the specified timeout interval, a C{TIMEDOUT} outcome is written to the outcome 
		list, and the method returns to the caller.
		
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
		specified timeout interval, a C{TIMEDOUT} outcome is written to the outcome list, and the method 
		returns to the caller.
		
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
		while 1:
			if os.path.exists(f):
				matches = getmatches(f, expr)
				if eval("%d %s" % (len(matches), condition)):
					log.info("Wait for signal in %s completed successfully", file)
					break
				
			currentTime = time.time()
			if currentTime > startTime + timeout:
				log.info("Wait for signal in %s timedout", file)
				log.info("Number of matches to the expression are %d" % len(matches))
				break
			time.sleep(poll)
		return matches


	def __del__(self):
		"""Class destructor which stops any running processes started by the class instance. 
				
		"""
		for process in self.processList:
			try:
				if process.running(): process.stop()
			except:
				 log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
		self.processList = []
		self.processCount = {}
