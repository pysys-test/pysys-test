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

"""Contains the OS-specific process wrapper subclass. 

@undocumented: EXPR
"""

import string, os.path, time, logging, sys, threading

if 'epydoc' not in sys.modules:
	import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes

if sys.version_info[0] == 2:
	import Queue
else:
	import queue as Queue

from pysys import log
from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *
from pysys.process.commonwrapper import CommonProcessWrapper, _stringToUnicode

# check for new lines on end of a string
EXPR = re.compile(".*\n$")


class ProcessWrapper(CommonProcessWrapper):
	"""Windows Process wrapper for process execution and management. 
	
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
	within the class instance, and these values can be accessed directly via it's object reference.  

	@ivar pid: The process id for a running or complete process (as set by the OS)
	@type pid: integer
	@ivar exitStatus: The process exit status for a completed process	
	@type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None, **kwargs):
		"""Create an instance of the process wrapper.
		
		@param command:  The full path to the command to execute
		@param arguments:  A list of arguments to the command
		@param environs:  A dictionary of environment variables (key, value) for the process context execution
		@param workingDir:  The working directory for the process
		@param state:  The state of the process (L{pysys.constants.FOREGROUND} or L{pysys.constants.BACKGROUND}
		@param timeout:  The timeout in seconds to be applied to the process
		@param stdout:  The full path to the filename to write the stdout of the process
		@param stderr:  The full path to the filename to write the sdterr of the process
		@param displayName: Display name for this process

		"""
		CommonProcessWrapper.__init__(self, command, arguments, environs, workingDir, 
			state, timeout, stdout, stderr, displayName, **kwargs)

		assert self.environs, 'Cannot start a process with no environment variables set; use createEnvirons to make a minimal set of env vars'

		# private instance variables
		self.__hProcess = None
		self.__hThread = None
		self.__tid = None
		
		self.__lock = threading.Lock() # to protect access to the fields that get updated
		
		# on Python 2, convert byte strings to unicode strings
		self.stdout = u'nul' if (not self.stdout) else _stringToUnicode(stdout)
		self.stderr = u'nul' if (not self.stderr) else _stringToUnicode(stderr)

		# these different field names are just retained for compatibility in case anyone is using them
		self.fStdout = self.stdout
		self.fStderr = self.stderr

	def writeStdin(self):
		"""Method to write to the process stdin pipe.
		
		"""
		while self._outQueue:
			try:
				data = self._outQueue.get(block=True, timeout=0.25)
			except Queue.Empty:
				if not self.running():
					break
			else:
				with self.__lock:
					if self.__stdin:
						win32file.WriteFile(self.__stdin, data, None)


	def __quotePath(self, input):
		"""Private method to escape a windows path according to documented guidelines for this OS.
		
		"""
		return '\"%s\"'%input.replace('"', '""')

	def startBackgroundProcess(self):
		"""Method to start a process running in the background.
		
		"""	
		with process_lock:
			# security attributes for pipes
			sAttrs = win32security.SECURITY_ATTRIBUTES()
			sAttrs.bInheritHandle = 1
	
			# create pipes for the process to write to
			hStdin_r, hStdin = win32pipe.CreatePipe(sAttrs, 0)
			hStdout = win32file.CreateFile(_stringToUnicode(self.stdout), win32file.GENERIC_WRITE | win32file.GENERIC_READ,
			   win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
			   sAttrs, win32file.CREATE_ALWAYS, win32file.FILE_ATTRIBUTE_NORMAL, None)
			hStderr = win32file.CreateFile(_stringToUnicode(self.stderr), win32file.GENERIC_WRITE | win32file.GENERIC_READ,
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
			except pywintypes.error as e:
				raise ProcessError("Error creating process %s: %s" % (old_command, e))

			win32file.CloseHandle(hStdin_r)
			win32file.CloseHandle(hStdout)
			win32file.CloseHandle(hStderr)

			# set the handle to the stdin of the process 
			self.__stdin = hStdin
		

	def setExitStatus(self):
		"""Method to set the exit status of the process.
		
		"""
		with self.__lock:
			if self.exitStatus is not None: return self.exitStatus
			exitStatus = win32process.GetExitCodeProcess(self.__hProcess)
			if exitStatus != win32con.STILL_ACTIVE:
				try:
					if self.__hProcess: win32file.CloseHandle(self.__hProcess)
					if self.__hThread: win32file.CloseHandle(self.__hThread)
					if self.__stdin: win32file.CloseHandle(self.__stdin)
				except Exception as e:
					# these failed sometimes with 'handle is invalid', probably due to interference of stdin writer thread
					log.warning('Could not close process and thread handles for process %s: %s', self.pid, e)
				self.__stdin = self.__hThread = self.__hProcess = None
				self._outQueue = None
				self.exitStatus = exitStatus
			
			return self.exitStatus


	def stop(self, timeout=TIMEOUTS['WaitForProcessStop']): 
		"""Stop a process running.
		
		@raise ProcessError: Raised if an error occurred whilst trying to stop the process
		
		"""
		try:
			with self.__lock:
				if self.exitStatus is not None: return 
				win32api.TerminateProcess(self.__hProcess,0)
			
			self.wait(timeout=timeout)
		except Exception:
			raise ProcessError("Error stopping process")
		

	def signal(self, signal):
		"""Send a signal to a running process. 
	
		Note that this method is not implemented for win32 processes, and calling this on a 
		win32 OS will raise a NotImplementedError.
	
		@param signal:  The integer signal to send to the process
		@raise ProcessError: Raised if an error occurred whilst trying to signal the process
		
		"""
		raise NotImplementedError("Unable to send a signal to a windows process")


