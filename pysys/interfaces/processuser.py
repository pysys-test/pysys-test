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

import os, time

from pysys.constants import *

log = logging.getLogger('pysys.interfaces.processuser')
log.setLevel(logging.NOTSET)


class ProcessUserInterface:
	"""Abstract class for modules which provide methods over interacting with processes.
	
	Th ProcessUserInterface class can be thought of as defining the contract that the 
	L{pysys.baserunner.BaseRunner} and L{pysys.basetest.BaseTest} classes must implement to provide 
	utilities for controlling and interacting with processes (e.g. starting, stopping etc). As these 
	classes implement this interface, any application helper classes that are written to make use of 
	the base class functionalility can be used both within extensions to the BaseRunner and BaseTest 
	classes. This is not really an interface class, but an abstract class, as where possible methods 
	of this class are implemented to facilitate code-reuse. 
	
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
		if name == "input" | name == "output":
			return os.getcwd()
		else:
			raise AttributeError("Unknown class attrbite")


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
		
	
	def startProcess(self, command, arguments, environs={}, workingDir=None, state=FOREGROUND, timeout=None, stdout=None, stderr=None, displayName=None):
		"""Start a process running in the foreground or background, and return the process handle.
				
		@param command: The command to start the process (should include the full path)
		@param arguments: A list of arguments to pass to the command
		@param environs: A dictionary of the environment to run the process in (defaults to clean environment)
		@param workingDir: The working directory for the process to run in
		@param state: Run the process either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		@param timeout: The timeout period after which to termintate processes running in the C{FOREGROUND}
		@param stdout: The filename used to capture the stdout of the process
		@param stderr: The filename user to capture the stderr of the process
		@param displayName: Logical name of the process used for display and reference counting (defaults to the basename of the command)
		@return: The process handle of the process (L{pysys.process.helper.ProcessWrapper})
		@rtype: handle

		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def stopProcess(self, process):
		"""Send a soft or hard kill to a running process to stop it's execution.
	
		@param process: The process handle returned from the L{startProcess()} method
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def signalProcess(self, process, signal):
		"""Send a signal to a running process (Unix only).

		@param process: The process handle returned from the L{startProcess()} method
		@param signal: The integer value of the signal to send
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess()} method
		@param timeout: The timeout value in seconds to wait before returning
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def writeProcess(self, process, data, addNewLine=TRUE):
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
		
		exit = FALSE
		startTime = time.time()
		while not exit:
			try:
				s.connect((host, port))
				exit = TRUE
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
		if filedir == None: filedir = self.output
		f = os.path.join(filedir, file)
		
		log.debug("Performing wait for file creation:")
		log.debug("  file:       %s" % file)
		log.debug("  filedir:    %s" % filedir)
		
		exit = FALSE
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
			
