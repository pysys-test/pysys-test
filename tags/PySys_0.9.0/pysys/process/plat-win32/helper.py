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

import string, os.path, time, thread, logging, Queue
import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes

from pysys import log
from pysys.constants import *
from pysys.exceptions import *

# check for new lines on end of a string
EXPR = re.compile(".*\n$")


class ProcessWrapper:
	"""Process wrapper for process execution and management. 
	
	The process wrapper provides the ability to start and stop an external process, setting 
	the process environment, working directory and state i.e. a foreground process in which case 
	a call to the L{start} method will not return until the process has exited, or a background 
	process in which case the process is started in a separate thread allowing concurrent execution 
	within the testcase. Processes started in the foreground can have a timeout associated with them, such
	that should the timeout be exceeded, the process will be terminated and control	passed back to the 
	caller of the method. The wrapper additionally allows control over logging of the process stdout 
	and stderr to file, and writing to the process stdin.
	
	Usage of the class is to first create an instance, setting all runtime parameters of the process 
	as data attributes to the class instance via the constructor. The process can then be started 
	and stopped via the L{start} and L{stop} methods of the class, as well as interrogated for 
	its executing status via the L{running} method, and waited for its completion via the L{wait}
	method. During process execution the C{self.pid} and C{seld.exitStatus} data attributes are set 
	within the class instance, and these values can be accessed directly via its object reference.  

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
		self.environs = {}
		for key in environs: self.environs[self.__stringToUnicode(key)] = self.__stringToUnicode(environs[key])
		self.workingDir = workingDir
		self.state = state
		self.timeout = timeout

		# 'publicly' available data attributes set on execution
		self.pid = None
		self.exitStatus = None

		# private instance variables
		self.__hProcess = None
		self.__hThread = None
		self.__tid = None
		self.__outQueue = Queue.Queue()
		
		# set the stdout|err file handles
		self.fStdout = 'nul'
		self.fStderr = 'nul'
		try:
			if stdout is not None: self.fStdout = self.__stringToUnicode(stdout)
		except:
			log.info("Unable to create file to capture stdout - using the null device")
		try:
			if stderr is not None: self.fStderr = self.__stringToUnicode(stderr)
		except:
			log.info("Unable to create file to capture stdout - using the null device")

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", stdout)
		log.debug("  stdout       : %s", stderr)
		keys=self.environs.keys()
		keys.sort()
		for e in keys: log.debug("  environment  : %s=%s", e, self.environs[e])


	def __stringToUnicode(self, s):
		""" Converts a unicode string or a utf-8 bit string into a unicode string. 
		
		"""
		if isinstance(s, unicode):
			return s
		else:
			return unicode(s, "utf8")


	def __writeStdin(self, hStdin):
		"""Private method to write to the process stdin pipe.
		
		"""
		while 1:
			try:
				data = self.__outQueue.get(block=True, timeout=0.25)
			except Queue.Empty:
				if not self.running(): break
			else:
				win32file.WriteFile(hStdin, data, None)


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
		hStdout = win32file.CreateFile(self.__stringToUnicode(self.fStdout), win32file.GENERIC_WRITE | win32file.GENERIC_READ,
									   win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
									   sAttrs, win32file.CREATE_ALWAYS, win32file.FILE_ATTRIBUTE_NORMAL, None)
		hStderr = win32file.CreateFile(self.__stringToUnicode(self.fStderr), win32file.GENERIC_WRITE | win32file.GENERIC_READ,
									   win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
									   sAttrs, win32file.CREATE_ALWAYS, win32file.FILE_ATTRIBUTE_NORMAL, None)

		# set the info structure for the new process.
		StartupInfo = win32process.STARTUPINFO()
		StartupInfo.hStdInput  = hStdin_r
		StartupInfo.hStdOutput = hStdout
		StartupInfo.hStdError  = hStderr
		StartupInfo.dwFlags = win32process.STARTF_USESTDHANDLES

		# Create new handles for the thread ends of the pipes. The duplicated handles will
		# have their inheritence properties set to false so that any children inheriting these
		# handles will not have non-closeable handles to the pipes
		pid = win32api.GetCurrentProcess()
		tmp = win32api.DuplicateHandle(pid, hStdin, pid, 0, 0, win32con.DUPLICATE_SAME_ACCESS)
		win32file.CloseHandle(hStdin)
		hStdin = tmp

		# start the process, and close down the copies of the process handles
		# we have open after the process creation (no longer needed here)
		old_command = command = self.__quotePath(self.command)
		for arg in self.arguments: command = '%s %s' % (command, self.__quotePath(arg))
		try:
			self.__hProcess, self.__hThread, self.pid, self.__tid = win32process.CreateProcess( None, command, None, None, 1, 0, self.environs, os.path.normpath(self.workingDir), StartupInfo)
		except pywintypes.error:
			raise ProcessError, "Error creating process %s" % (old_command)

		win32file.CloseHandle(hStdin_r)
		win32file.CloseHandle(hStdout)
		win32file.CloseHandle(hStderr)

		# set the handle to the stdin of the process 
		self.__stdin = hStdin
		
		# check to see if the process is running. If it is kick off the threads to collect
		# the stdout and stderr
		if self.running():					
			thread.start_new_thread(self.__writeStdin, (hStdin, ))


	def __startForegroundProcess(self):
		"""Private method to start a process running in the foreground.
		
		"""
		self.__startBackgroundProcess()
		self.wait(self.timeout)


	def __setExitStatus(self):
		"""Private method to set the exit status of the process.
		
		"""
		if self.exitStatus is not None: return 
		exitStatus = win32process.GetExitCodeProcess(self.__hProcess)
		if exitStatus != win32con.STILL_ACTIVE:
			self.exitStatus = exitStatus


	def write(self, data, addNewLine=True):
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
		
		@return: The running status (True / False)
		@rtype: integer
		
		"""
		self.__setExitStatus()
		if self.exitStatus is not None: return False
		return True


	def wait(self, timeout):
		"""Wait for a process to complete execution.
		
		The method will block until either the process is no longer running, or the timeout 
		is exceeded. Note that the method will not terminate the process if the timeout is 
		exceeded. 
		
		@param timeout: The timeout to wait in seconds
		@raise ProcessTimeout: Raised if the timeout is exceeded.
		
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
		if self.exitStatus is not None: return 
		try:
			win32api.TerminateProcess(self.__hProcess,0)
			self.wait(timeout=0.5)
		except:
			raise ProcessError, "Error stopping process"
		

	def signal(self, signal):
		"""Send a signal to a running process. 
	
		Note that this method is not implemented for win32 processes, and calling this on a 
		win32 OS will raise a NotImplementedError.
	
		@param signal:  The integer signal to send to the process
		@raise ProcessError: Raised if an error occurred whilst trying to signal the process
		
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




					   
