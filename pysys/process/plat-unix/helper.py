#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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

"""Contains the OS-specific ProcessWrapper subclass. 

:meta private: No reason to publically document this. 

The import path of the helper and monitor modules is set up
at runtime so as to select either the Win32 modules (located in pysys.process.plat-win32), or the 
unix modules (located in pysys.process.plat-unix); both modules are written to display common 
functionality in order to provide a unified abstraction where the user is not required to select the 
correct modules based on their current operation system.

"""

import signal, time, copy, errno, threading, sys
import select
import queue as Queue

from pysys import log
from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *
from pysys.process import Process
import pysys.process.user as processuser # can't import ProcessUser class itself without circular dependency

PYSYS_DISABLE_PROCESS_GROUP_CLEANUP = os.getenv('PYSYS_DISABLE_PROCESS_GROUP_CLEANUP','').lower()=='true' # undocumented option for disabling this when executed within another framework

class ProcessImpl(Process):
	"""Unix process wrapper for process execution and management. 
	
	The unix process wrapper provides the ability to start and stop an external process, setting 
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

	:ivar pid: The process id for a running or complete process (as set by the OS)
	:type pid: integer
	:ivar exitStatus: The process exit status for a completed process	
	:type exitStatus: integer

	:ivar stdout: The full path to the filename to write the stdout of the process
	:type stdout: string

	:ivar stderr: The full path to the filename to write the stderr of the process
	:type stderr: string
	
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
		
		if self.stdout is None: self.stdout = '/dev/null'
		if self.stderr is None: self.stderr = '/dev/null'

		# private instance variables
		self.__lock = threading.Lock() # to protect access to the fields that get updated while process is running
		self.pidfd = None

	def _writeStdin(self, data):
		with self.__lock:
			if not self.__stdin: return
			if data is None:
				os.close(self.__stdin)
			else:
				os.write(self.__stdin, data)	
	

	def startBackgroundProcess(self):
		"""Method to start a process running in the background.
		
		"""
		with process_lock:

			try:
				stdin_r, stdin_w = os.pipe()
				self.pid = os.fork()

				if self.pid == 0: # pragma: no cover
					# create a new process group (same id as this pid) containing this new process, which we can use to kill grandchildren
					if not PYSYS_DISABLE_PROCESS_GROUP_CLEANUP:
						os.setpgrp()
				
					# change working directory of the child process
					os.chdir(self.workingDir)
						
					# duplicate the read end of the pipe to stdin	
					os.dup2(stdin_r, 0)

					# create and duplicate stdout and stderr to open file handles
					stdout_w = os.open(self.stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
					stderr_w = os.open(self.stderr, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
					os.dup2(stdout_w, 1)
					os.dup2(stderr_w, 2)

					# close any stray file descriptors (within reason)
					try:
						maxfd = os.sysconf("SC_OPEN_MAX")
					except Exception:
						maxfd=256
					os.closerange(3, maxfd)
				
					# execve the process to start it
					arguments = copy.copy(self.arguments)
					arguments.insert(0, os.path.basename(self.command))
					os.execve(self.command, arguments, self.environs)
				else:
					# close the read end of the pipe in the parent
					# and start a thread to write to the write end
					os.close(stdin_r)
					self.__stdin = stdin_w

					try:
						if hasattr(os, 'pidfd_open'): # only in Python 3.9+ and Linux kernel 5.3+ (e.g. RHEL9)
							self.pidfd = os.pidfd_open(self.pid)
							if self.pidfd == -1: self.pidfd = None
					except Exception as ex:
						log.debug('Failed to call os.pidfd_open: %r', ex)
			except Exception as ex:
				if self.pid == 0: 
					sys.stderr.write('Failed with: %s\n'%ex)
					sys.stderr.flush()
					os._exit(os.EX_OSERR)	

		if not self.running() and self.exitStatus == os.EX_OSERR:
			raise ProcessError("Error creating process %s" % (self.command))


	def _pollWaitUnlessProcessTerminated(self):
		# While waiting for process to terminate, modern Linux kernels (5.3+) give us a way to block for completion without polling, so we 
		# can use a larger timeout to avoid wasting time in the Python GIL (but not so large as to stop us from checking for abort
		owner = self.owner
		ProcessUser = processuser.ProcessUser
		if self.pidfd and ProcessUser.isRunnerAbortingHandle:
			if owner is not None and ProcessUser.isRunnerAborting is True and owner.isCleanupInProgress is False: raise KeyboardInterrupt()

			waitobjects = [ ProcessUser.isRunnerAbortingHandle, self.pidfd]

			pollTimeoutMillis = 3000
			if select.select(waitobjects, [], [], pollTimeoutMillis/1000.0)[0]: # if objects were signalled or got anything other than timeout/block, something was signalled so we won't be doing this again
				with self.__lock:
					# this is a fail-safe to ensure we do not spin calling select if some unexpected error occurred OR if we've been interrupt-terminated but are executing cleanup
					if self.pidfd: os.close(self.pidfd)
					self.pidfd = None

			if owner is not None and processuser.ProcessUser.isRunnerAborting is True and owner.isCleanupInProgress is False: raise KeyboardInterrupt()
			return
		
		self._pollWait(0.05) # fallback to a fixed sleep to avoid spinning if an unexpected return code is returned

	def setExitStatus(self):
		"""Tests whether the process has terminated yet, and updates and returns the exit status if it has. 
		"""
		with self.__lock:
			if self.exitStatus is not None: return self.exitStatus
	
			retries = 3
			while retries > 0:	
				try:
					pid, status = os.waitpid(self.pid, os.WNOHANG)
					if pid == self.pid:
						if os.WIFEXITED(status):
							self.exitStatus = os.WEXITSTATUS(status)
						elif os.WIFSIGNALED(status):
							self.exitStatus = os.WTERMSIG(status)
						else:
							self.exitStatus = status
						self._outQueue = None
					retries=0
				except OSError as e: # pragma: no cover
					if e.errno == errno.ECHILD:
						time.sleep(0.01)
						retries=retries-1
					else:
						retries=0
			
			if self.exitStatus != None:
				if self.__stdin:
					try: os.close(self.__stdin)
					except Exception: pass # just being conservative, should never happen
					self.__stdin = None # MUST not close this more than once
				if self.pidfd: 
					os.close(self.pidfd)
					self.pidfd = None

			
			return self.exitStatus


	def stop(self, timeout=TIMEOUTS['WaitForProcessStop'], hard=False):
		"""Stop a process running.
		
		Uses SIGTERM to give processes a chance to gracefully exit including dump code coverage information if needed. 
		
		@raise ProcessError: Raised if an error occurred whilst trying to stop the process
		
		"""
		# PySys has always done a non-hard SIGTERM on Unix; so far this seems ok but could cause problems for 
		# poorly behaved processes that don't SIGTERM cleanly
		
		sig = signal.SIGKILL if hard else signal.SIGTERM
		
		try:
			with self.__lock:
				if self.exitStatus is not None: return 
				
				# do the kill before the killpg, as there's a small race in which we might try to stop a process 
				# before it has added itself to its own process group, in which case this is essential to avoid 
				# leaking
				os.kill(self.pid, sig)
				
				# nb assuming setpgrp was called when we forked, this will signal the entire process group, 
				# so any children are also killed; small chance this could fail if the process was stopped 
				# before it had a chance to create its process group
				if not self.disableKillingChildProcesses:
					try:
						os.killpg(self.pid, sig)
					except Exception as ex: # pragma: no cover
						# Best not to worry about these
						log.debug('Failed to kill process group (but process itself was killed fine) for %s: %s', self, ex)
			
			try:
				self.wait(timeout=timeout)
			except BaseException as ex: # pragma: no cover
				# catch baseexception as we need to do this killing even for stuff like KeyboardInterrupt and SystemExit
				# if it times out on SIGTERM, do our best to SIGKILL it anyway to avoid leaking processes, but still report as an error
				if sig != signal.SIGKILL:
					log.warning('Failed to SIGTERM process %r, will now SIGKILL the process group before re-raising the exception', self)
					try:
						os.killpg(self.pid, signal.SIGKILL)
					except Exception as ex2:
						log.debug('Failed to SIGKILL process group %r: %s', self, ex2)
				
				raise
		except Exception as ex: # pragma: no cover
			log.debug('Failed to stop process %r: ', self, exc_info=True)
			raise ProcessError("Error stopping process %r due to %s: %s"%(self, type(ex).__name__, ex))

ProcessWrapper = ProcessImpl # old name for compatibility

log.debug("OS and python supports pidfd_open: %s", hasattr(os, 'pidfd_open'))

