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

from pysys.constants import *

class ProcessHelperInterface:
	"""Interface class for modules which provide methods over interacting with processes.
	
	Th ProcessHelperInterface class can be considered setting the contract that the 
	L{pysys.baserunner.BaseRunner} and L{pysys.basetest.BaseTest} classes ,must implement to 
	provide utilities for interacting with processes (e.g. starting, stoppind, waiting 
	etc). As these base classes implement this interface, any application helper classes 
	that are written to make use of the base class functionalility can be used both within 
	extensions to the BaseRunner and BaseTest classes.
	
	"""
	
	def getInstanceCount(self, displayName):
		"""Return the number of processes started within the class instance matching the supplied displayName.
		
		@param displayName: The process display name
		@return: The number of processes started matching the command basename
		@rtype:  integer
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"

	
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


	def writeProcess(self, process, data, addNewLine=TRUE):
		"""Write data to the stdin of a process.
		
		@param process: The process handle returned from the L{startProcess()} method
		@param data: The data to write to the process		
		@param addNewLine: True if a new line character is to be added to the end of the data string
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def waitProcess(self, process, timeout):
		"""Wait for a process to terminate, return on termination or expiry of the timeout.
	
		@param process: The process handle returned from the L{startProcess()} method
		@param timeout: The timeout value in seconds to wait before returning
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def waitForSocket(self, port, host='localhost', timeout=TIMEOUTS['WaitForSocket']):
		"""Wait for a socket connection to be established.
				
		@param port: The port value in the socket host:port pair
		@param host: The host value in the socket host:port pair
		@param timeout: The timeout in seconds to wait for connection to the socket
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"


	def waitForFile(self, file, filedir=None, timeout=TIMEOUTS['WaitForFile']):
		"""Wait for a file to be written to disk.
		
		@param file: The basename of the file used to wait to be created
		@param filedir: The dirname of the file 
		@param timeout: The timeout in seconds to wait for the file to be created
		
		"""
		raise NotImplementedError, "The method must be implemented by a subclass"
		
