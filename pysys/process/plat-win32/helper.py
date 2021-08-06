#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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

:meta private: No reason to publically document this. 
"""

import string, os.path, time, logging, sys, threading, platform

import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes, win32job

if sys.version_info[0] == 2:
	import Queue
else:
	import queue as Queue

from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *
from pysys.process import Process

# check for new lines on end of a string
EXPR = re.compile(".*\n$")
log = logging.getLogger('pysys.process')

try:
	IS_PRE_WINDOWS_8 = int(platform.version().split('.')[0]) < 8
except Exception: # pragma: no cover
	IS_PRE_WINDOWS_8 = False
	
class ProcessImpl(Process):
	"""Windows Process wrapper/implementation for process execution and management. 
	
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

	:ivar pid: The process id for a running or complete process (as set by the OS)
	:type pid: integer
	:ivar exitStatus: The process exit status for a completed process	
	:type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None, **kwargs):
		"""Create an instance of the process wrapper.
		
		:param command:  The full path to the command to execute
		:param arguments:  A list of arguments to the command
		:param environs:  A dictionary of environment variables (key, value) for the process context execution
		:param workingDir:  The working directory for the process
		:param state:  The state of the process (L{pysys.constants.FOREGROUND} or L{pysys.constants.BACKGROUND}
		:param timeout:  The timeout in seconds to be applied to the process
		:param stdout:  The full path to the filename to write the stdout of the process
		:param stderr:  The full path to the filename to write the sdterr of the process
		:param displayName: Display name for this process

		"""
		
		Process.__init__(self, command, arguments, environs, workingDir, 
			state, timeout, stdout, stderr, displayName, **kwargs)

		self.disableKillingChildProcesses = self.info.get('__pysys.disableKillingChildProcesses', False) # currently undocumented, just an emergency escape hatch for now

		assert self.environs, 'Cannot start a process with no environment variables set; use createEnvirons to make a minimal set of env vars'

		# private instance variables
		self.__hProcess = None
		self.__hThread = None
		self.__tid = None
		
		self.__lock = threading.Lock() # to protect access to the fields that get updated

		self.stdout = u'nul' if (not self.stdout) else self.stdout.replace('/',os.sep)
		self.stderr = u'nul' if (not self.stderr) else self.stderr.replace('/',os.sep)
		

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
			hStdout = win32file.CreateFile(self.stdout, win32file.GENERIC_WRITE | win32file.GENERIC_READ,
			   win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
			   sAttrs, win32file.CREATE_ALWAYS, win32file.FILE_ATTRIBUTE_NORMAL, None)
			hStderr = win32file.CreateFile(self.stderr, win32file.GENERIC_WRITE | win32file.GENERIC_READ,
			   win32file.FILE_SHARE_DELETE | win32file.FILE_SHARE_READ | win32file.FILE_SHARE_WRITE,
			   sAttrs, win32file.CREATE_ALWAYS, win32file.FILE_ATTRIBUTE_NORMAL, None)
			  
			try:

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
				
				# Windows CreateProcess maximum lpCommandLine length is 32,768
				# http://msdn.microsoft.com/en-us/library/ms682425%28VS.85%29.aspx
				if len(command)>=32768: # pragma: no cover
					raise ValueError("Command line length exceeded 32768 characters: %s..."%command[:1000])

				dwCreationFlags = 0
				if IS_PRE_WINDOWS_8: # pragma: no cover
					# In case PySys is itself running in a job, might need to explicitly breakaway from it so we can give 
					# it its own, but only for old pre-windows 8/2012, which support nested jobs
					dwCreationFlags  = dwCreationFlags | win32process.CREATE_BREAKAWAY_FROM_JOB
				
				if self.command.lower().endswith(('.bat', '.cmd')):
					# If we don't start suspended there's a slight race condition but due to some issues with 
					# initially-suspended processes hanging (seen many years ago), to be safe, only bother to close the 
					# race condition for shell scripts (which is the main use case for this anyway)
					dwCreationFlags = dwCreationFlags | win32con.CREATE_SUSPENDED

				self.__job = self._createParentJob()

				try:
					self.__hProcess, self.__hThread, self.pid, self.__tid = win32process.CreateProcess( None, command, None, None, 1, 
						dwCreationFlags, self.environs, os.path.normpath(self.workingDir), StartupInfo)
				except pywintypes.error as e:
					raise ProcessError("Error creating process %s: %s" % (old_command, e))

				try:
					if not self.disableKillingChildProcesses:
						win32job.AssignProcessToJobObject(self.__job, self.__hProcess)
					else: 
						self.__job = None # pragma: no cover
				except Exception as e: # pragma: no cover
					# Shouldn't fail unless process already terminated (which can happen since 
					# if we didn't use SUSPENDED there's an inherent race here)
					if win32process.GetExitCodeProcess(self.__hProcess)==win32con.STILL_ACTIVE:
						log.warning('Failed to associate process %s with new job: %s (this may prevent automatic cleanup of child processes)' %(self, e))
					
					# force use of TerminateProcess not TerminateJobObject if this failed
					self.__job = None
				
				if (dwCreationFlags & win32con.CREATE_SUSPENDED) != 0:
					win32process.ResumeThread(self.__hThread)
			finally:
				win32file.CloseHandle(hStdin_r)
				win32file.CloseHandle(hStdout)
				win32file.CloseHandle(hStderr)

			# set the handle to the stdin of the process 
			self.__stdin = hStdin

	def _createParentJob(self):
		# Create a new job that this process will be assigned to.
		job_name = '' # must be anonymous otherwise we'd get conflicts
		security_attrs = win32security.SECURITY_ATTRIBUTES()
		security_attrs.bInheritHandle = 1
		job = win32job.CreateJobObject(security_attrs, job_name)
		extended_limits = win32job.QueryInformationJobObject(job, win32job.JobObjectExtendedLimitInformation)
		extended_limits['BasicLimitInformation']['LimitFlags'] = win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
		
		win32job.SetInformationJobObject(job, win32job.JobObjectExtendedLimitInformation, extended_limits)
		return job


	def setExitStatus(self):
		"""Tests whether the process has terminated yet, and updates and returns the exit status if it has. 
		"""
		with self.__lock:
			if self.exitStatus is not None: return self.exitStatus
			exitStatus = win32process.GetExitCodeProcess(self.__hProcess)
			if exitStatus != win32con.STILL_ACTIVE:
				try:
					if self.__hProcess: win32file.CloseHandle(self.__hProcess)
					if self.__hThread: win32file.CloseHandle(self.__hThread)
					if self.__stdin: win32file.CloseHandle(self.__stdin)
				except Exception as e: # pragma: no cover
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
				
				try:
					if self.__job:
						win32job.TerminateJobObject(self.__job, 0)
					else:
						win32process.TerminateProcess(self.__hProcess, 0) # pragma: no cover

				except Exception as e: # pragma: no cover
					# ignore errors unless the process is still running
					if win32process.GetExitCodeProcess(self.hProcess)==win32con.STILL_ACTIVE:
						log.warning('Failed to terminate job object for process %s: %s'%(self, e))

						# try this approach instead
						win32process.TerminateProcess(self.__hProcess, 0)

			self.wait(timeout=timeout)
		except Exception as ex: # pragma: no cover
			raise ProcessError("Error stopping process: %s"%ex)

ProcessWrapper = ProcessImpl # old name for compatibility
