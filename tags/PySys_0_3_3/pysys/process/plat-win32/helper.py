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

import string, os.path, time, thread, logging, Queue
import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes

from pysys.constants import *
from pysys.exceptions import *

# create the class logger
log = logging.getLogger('pysys.process.helper')

# check for new lines on end of a string
EXPR = re.compile(".*\n$")


class NullDevice:
	"""Class to implement the write and flush methods of a file descriptor. 
	
	Used as a representation of the null device, so that writing to this device
	produces no output.
	
	"""
	def write(self, str):
		"""Called to write a string value to the device (no-op).
		
		@param str: The string to write to the null device
		
		"""
		pass

	def flush(self):
		"""Called to flush the device (no-op).
		
		"""
		pass
	

class ProcessWrapper:
	"""Win32 process wrapper for process execution and management. 
	
	The win32 process wrapper provides the ability to start and stop an external process, setting 
	the process environment, working directory and state i.e. a foreground process in which case 
	a call to the L{start()} method will not return until the process has exited, or a background 
	process in which case the process is started in a separate thread allowing concurrent execution 
	within the testcase. Processes started in the foreground can have a timeout associated with them, such
	that should the timeout be exceeded, the process will be terminated and control	passed back to the 
	caller of the method. The wrapper additionally allows control over logging of the process stdout 
	and stderr to file, and writing to the process stdin.
	
	Usage of the class is to first create an instance, setting all runtime parameters of the process 
	as data attributes to the class instance via the constructor. The process can then be started 
	and stopped via the L{start()} and L{stop()} methods of the class, as well as interrogated for 
	its executing status via the L{running()} method, and waited for its completion via the L{wait()}
	method. During process execution the C{self.pid} and C{seld.exitStatus} data attributes are set 
	within the class instance, and these values can be accessed directly via it's object reference.  

	@ivar pid: The process id for a running or complete process (as set by the OS)
	@type pid: integer
	@ivar exitStatus: The process exit status for a completed process	
	@type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None):
		"""Create an instance of the process wrapper.
		
		@param command:  The full path to the command to execute
		@param arguments:  A list of arguments to the command
		@param environs:  A dictionary of environment variables (key, value) for the process context execution
		@param workingDir:  The working directory for the process
		@param state:  The state of the process (L{pysys.constants.FOREGROUND} or L{pysys.constants.BACKGROUND}
		@param timeout:  The timeout in seconds to be applied to the process
		@param stdout:  The full path to the filename to write the stdout of the process
		@param stderr:  The full path to the filename to write the sdterr of the process

		"""
		self.command = command
		self.arguments = arguments
		self.environs = environs
		self.workingDir = workingDir
		self.state = state
		self.timeout = timeout
		self.stdout = stdout
		self.stderr = stderr	

		# 'publicly' available data attributes set on execution
		self.pid = None
		self.exitStatus = None

		# private instance variables
		self.__hProcess = None
		self.__hThread = None
		self.__tid = None
		self.__outQueue = Queue.Queue()
		
		# set the stdout|err file handles
		self.fStdout = NullDevice()
		self.fStderr = NullDevice()
		try:
			if self.stdout != None: self.fStdout = open(self.stdout, 'w', 0)
		except:
			log.info("Unable to create file to capture stdout - using the null device")
		try:
			if self.stderr != None: self.fStderr = open(self.stderr, 'w', 0)
		except:
			log.info("Unable to create file to capture stdout - using the null device")

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", self.stdout)
		log.debug("  stdout       : %s", self.stderr)
		for e in self.environs.keys(): log.debug("  environment  : %s=%s", e, environs[e])


	def __collectStdout(self, hStdout, fStdout):	
		"""Private method to read from the process stdout pipe and write to file.
		
		"""
		buffer = win32file.AllocateReadBuffer(200)
		while 1:
			try:
				res, str = win32file.ReadFile(hStdout, buffer)
				if res == 0:
					str = string.replace(str, "\r\n", "\n")
					self.fStdout.write(str)
			except:
				if not self.running(): break


	def __collectStderr(self, hStderr, fStderr):
		"""Private method to read from the process stderr pipe and write to file.
		
		"""
		buffer = win32file.AllocateReadBuffer(200)
		while 1:
			try:
				res, str = win32file.ReadFile(hStderr, buffer)
		  		if res == 0: 
				  	str = string.replace(str, "\r\n", "\n")
					fStderr.write(str)
			except:
				if not self.running(): break


	def __writeStdin(self, hStdin):
		"""Private method to write to the process stdin pipe.
		
		"""
		while 1:
			try:
				try:
					data = self.__outQueue.get(block=True, timeout=0.25)
				except Queue.Empty:
					pass
				else:
					win32file.WriteFile(hStdin, data, None)
			except:
				if not self.running(): break


	def __quotePath(self, input):
		"""Private method to sanitise a windows path.
		
		"""
		i = input
		if i.find(' ') > 0:
			return '\"%s\"' % i
		else:
			return i


	def __startBackgroundProcess(self):
		"""Private method to start a process running in the background. 
		
		"""
		# security attributes for pipes
		sAttrs = win32security.SECURITY_ATTRIBUTES()
		sAttrs.bInheritHandle = 1
	
		# create pipes for the process to write to
		hStdin_r, hStdin = win32pipe.CreatePipe(sAttrs, 0)
		hStdout, hStdout_w = win32pipe.CreatePipe(sAttrs, 0)
		hStderr, hStderr_w = win32pipe.CreatePipe(sAttrs, 0)

		# set the info structure for the new process.
		StartupInfo = win32process.STARTUPINFO()
		StartupInfo.hStdInput  = hStdin_r
		StartupInfo.hStdOutput = hStdout_w
		StartupInfo.hStdError  = hStderr_w
		StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES

		# Create new handles for the thread ends of the pipes. The duplicated handles will
		# have their inheritence properties set to false so that any children inheriting these
		# handles will not have non-closeable handles to the pipes
		pid = win32api.GetCurrentProcess()
		tmp = win32api.DuplicateHandle(pid, hStdin, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
		win32file.CloseHandle(hStdin)
		hStdin = tmp
		tmp = win32api.DuplicateHandle(pid, hStdout, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
		win32file.CloseHandle(hStdout)
		hStdout = tmp
		tmp = win32api.DuplicateHandle(pid, hStderr, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
		win32file.CloseHandle(hStderr)
		hStderr = tmp

		# start the process, and close down the copies of the process handles
		# we have open after the process creation (no longer needed here)
		old_command = command = self.__quotePath(self.command)
		for arg in self.arguments: command = '%s %s' % (command, self.__quotePath(arg))
		try:
			self.__hProcess, self.__hThread, self.pid, self.__tid = win32process.CreateProcess( None, command, None, None, 1, 0, self.environs, os.path.normpath(self.workingDir), StartupInfo)
		except pywintypes.error:
			raise ProcessError, "Error creating process %s" % (old_command)

		win32file.CloseHandle(hStdin_r)
		win32file.CloseHandle(hStdout_w)
		win32file.CloseHandle(hStderr_w)
		
		# set the handle to the stdin of the process 
		self.__stdin = hStdin
		
		# check to see if the process is running. If it is kick off the threads to collect
		# the stdout and stderr
		if self.running():					
			thread.start_new_thread(self.__collectStdout, (hStdout, self.fStdout))
			thread.start_new_thread(self.__collectStderr, (hStderr, self.fStderr))
			thread.start_new_thread(self.__writeStdin, (hStdin, ))


	def __startForegroundProcess(self):
		"""Private method to start a process running in the foreground.
		
		"""
		self.__startBackgroundProcess()
		self.wait(self.timeout)


	def __setExitStatus(self):
		"""Private method to set the exit status of the process.
		
		"""
		if self.exitStatus != None: return 
		exitStatus = win32process.GetExitCodeProcess(self.__hProcess)
		if exitStatus != win32con.STILL_ACTIVE:
			self.exitStatus = exitStatus


	def write(self, data, addNewLine=TRUE):
		"""Write data to the stdin of the process.
		
		Note that when the addNewLine argument is set to true, if a new line does not 
		terminate the input data string, a newline character will be added. If one 
		already exists a new line character will not be added. Should you explicitly 
		require to add data without the method appending a new line charater set 
		addNewLine to false.
		
		@param data:       The data to write to the process stdout
		@param addNewLine: True if a new line character is to be added to the end of 
		                   the data string
		
		"""
		if addNewLine and not EXPR.search(data): data = "%s\n" % data
		self.__outQueue.put(data)


	def running(self):
		"""Check to see if a process is running, returning true if running.
		
		@return: The running status (L{pysys.constants.TRUE} / L{pysys.constants.FALSE})
		@rtype: integer
		
		"""
		self.__setExitStatus()
		if self.exitStatus != None: return FALSE
		return TRUE


	def wait(self, timeout):
		"""Wait for a process to complete execution.
		
		The method will block until either the process is no longer running, or the timeout 
		is exceeded. Note that the method will not terminate the process if the timeout is 
		exceeded. 
		
		@param timeout: The timeout to wait in seconds
		@raise Process Timeout: Raised if the timeout is exceeded.
		
		"""
		startTime = time.time()
		while self.running():
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					raise ProcessTimeout, "Process timedout"
			time.sleep(0.1)
		

	def stop(self): 
		"""Stop a process running.
		
		@raise ProcessError: Raised if an error occurred whilst trying to stop the process
		
		"""
		if self.exitStatus !=None: return 
		try:
			win32api.TerminateProcess(self.__hProcess,0)
			self.__setExitStatus()
		except:
			raise ProcessError, "Error stopping process"


	def signal(self):
		"""Send a signal to a running process. 
		
		This method is not implemented for the win32 process wrapper, though is required for 
		consistency with the unix process wrapper. Calling of this method will raise a 
		NotImplementedError.
		
		@raise NotImplementedError: Raised as it is not possible to send a signal to a win32 process
		
		"""
		raise NotImplementedError , "Unable to send a signal to a windows process"


	def start(self):
		"""Start a process using the runtime parameters set at instantiation.
		
		@raise ProcessError: Raised if there is an error creating the process
		@raise ProcessTimeout: Raised in the process timed out (foreground process only)
		
		"""
		if self.state == FOREGROUND:
			self.__startForegroundProcess()
		else:
			self.__startBackgroundProcess()
			time.sleep(1)




					   
