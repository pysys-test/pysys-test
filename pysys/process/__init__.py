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


"""
Process execution and monitoring implementations. 
"""

from pysys.constants import *

# set the modules to import when imported the pysys.process package
__all__ = [ "helper",
			"monitor", 
			"monitorimpl",
			"user", 
			"Process"]

# add to the __path__ to import the platform specific process.helper module
dirname = __path__[0]
if IS_WINDOWS:
	__path__.append(os.path.join(dirname, "plat-win32"))
else:
	__path__.append(os.path.join(dirname, "plat-unix"))


import os.path, time, threading, sys, locale
import logging
import shlex
import queue as Queue

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.pycompat import *
from pysys.internal.initlogging import pysysLogHandler

log = logging.getLogger('pysys.process')

class Process(object):
	"""Represents a process that PySys has started (or can start).
	
	A platform-specific implementation subclass of this interface is returned 
	by `pysys.process.user.ProcessUser.startProcess`.
	
	:ivar str ~.command:  The full path to the executable.
	:ivar list[str] ~.arguments:  A list of arguments to the command.
	:ivar dict(str,str) ~.environs:  A dictionary of environment variables (key, value) for the process context execution. 
	:ivar str ~.workingDir:  The working directory for the process
	:ivar ~.state: The state of the process.
	:vartype state: `pysys.constants.FOREGROUND` or `pysys.constants.BACKGROUND`
	:ivar int ~.timeout:  The time in seconds for a foreground process to complete.
	:ivar str ~.stdout: The full path to the filename to write the stdout of the process, or None for no stderr stream.
	:ivar str ~.stderr: The full path to the filename to write the stderr of the process, or None for no stderr stream. 
	:ivar str ~.displayName: Display name for this process (defaults to the basename if not explicitly specified). The 
		display name is returned by calling ``str()`` on this instance. The display name and pid are returned by 
		``repr()``.
	:ivar str expectedExitStatus: The condition string used to determine whether the exit status/code 
		returned by the process is correct, for example '==0'.

	:ivar int ~.pid: The process id for a running or complete process (as set by the OS), or None if it is not yet started.
	:ivar ProcessUser ~.owner: The owner object that is running this process. 
	:ivar int ~.exitStatus: The process exit status for a completed process (for many processes 0 represents success), 
		or None if it has not yet completed. 
	:ivar dict[str,obj] ~.info: A mutable dictionary of user-supplied information that was passed into startProcess, 
		for example port numbers, log file paths etc. 
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None, 
		expectedExitStatus=None, info={}, owner=None):
		
		self.displayName = displayName if displayName else os.path.basename(command)
		self.info = info
		self.command = os.path.normpath(command)
		if any(not isstring(arg) for arg in arguments):
			arguments = [str(arg) for arg in arguments]
		self.arguments = arguments
		
		self.environs = {}
		for key in environs: self.environs[key] = environs[key]
		self.workingDir = os.path.normpath(workingDir)
		self.state = state
		self.timeout = timeout
		self.expectedExitStatus = expectedExitStatus
		self.owner = owner # nb: this CAN be initialzied to None, e.g. when test frameworks instantiate ProcessWrapper directly without calling startProcess

		# 'publicly' available data attributes set on execution
		self.pid = None
		self.exitStatus = None
		
		# these may be further updated by the subclass
		self.stdout = stdout
		self.stderr = stderr

		# catch these common mistakes
		assert os.path.isdir(self.workingDir), 'Working directory for %s does not exist: %s'%(self.displayName, self.workingDir)
		if self.stdout: assert os.path.dirname(self.stdout)==self.workingDir or os.path.isdir(os.path.dirname(self.stdout)), 'Parent directory for stdout does not exist: %s'%self.stdout

		# print process debug information
		
		debuginfo = []

		if IS_WINDOWS or not hasattr(shlex, 'quote'):
			quotearg = lambda c: '"%s"'%c if ' ' in c else c
		else:
			quotearg = shlex.quote
		debuginfo.append("  command line : %s"%' '.join(quotearg(c) for c in [self.command]+self.arguments))
		for i, a in enumerate(self.arguments): debuginfo.append("    arg #%-2d    : %s"%( i+1, a) )
		
		debuginfo.append("  working dir  : %s"% self.workingDir)
		if IS_WINDOWS and len(self.workingDir) > 256-30:
			debuginfo.append("    NB: length of working dir is %d (Windows MAX_PATH limit is 256 chars)" % len(self.workingDir))
		debuginfo.append("  stdout       : %s"% stdout)
		debuginfo.append("  stderr       : %s"% stderr)
		keys=list(self.environs.keys())
		keys.sort()
		defaultenv = []
		for e in keys: 
			value = self.environs[e]
			if value == os.environ.get(e, None): # having all the default env vars repeated for every process makes it hard to see what's what
				defaultenv.append(e)
				continue
			debuginfo.append("  environment  : %s=%s"%( e, value) )
			if 'PATH' in e.upper() and e.upper() not in ['PATHEXT']:
				# it's worth paths/classpaths/pythonpaths as they're often long and quite hard to spot differences otherwise
				pathelements = value.split(';' if ';' in value else os.pathsep)
				if len(pathelements)>1:
					for i, pathelement in enumerate(pathelements):
						#                         : ABC=def
						debuginfo.append("                   #%-2d %s"%( i+1, pathelement))
		if defaultenv: debuginfo.append("  environment  : +inherited default environment variables: %s"%( ', '.join(defaultenv)) )
		if info: debuginfo.append("  info         : %s"% info)

		log.debug("Process parameters for %s\n%s", self, '\n'.join(d for d in debuginfo))

		# private
		self._outQueue = None

		self._pollWait = time.sleep if self.owner is None else self.owner.pollWait


	def __str__(self): return self.displayName
	def __repr__(self): return '%s (pid %s)'%(self.displayName, self.pid)

	# these abstract methods must be implemented by subclasses; no need to publically document
	def setExitStatus(self): raise Exception('Not implemented')
	def startBackgroundProcess(self): raise Exception('Not implemented')
	def stop(self, timeout=TIMEOUTS['WaitForProcessStop'], hard=False): 
		"""Stop a running process and wait until it has finished.
		
		Does nothing if the process is not running. 
		
		On Windows, this uses TerminateProcess, on Linux this sends a SIGTERM signal (which allows the process a chance 
		to exit gracefully including possibly dumping code coverage output) unless the ``hard=True`` parameter is specified. 
		
		:param bool hard: Set to True to use a hard termination (e.g. SIGKILL). 
		:param float timeout: The time to wait for the process to complete before raising an exception. 
		@raise pysys.exceptions.ProcessError: Raised if an error occurred whilst trying to stop the process.		
		"""
		raise Exception('Not implemented')
		
	def signal(self, signal): 
		"""Send a signal to a running process. 
	
		Typically this uses ``os.kill`` to send the signal. 
	
		:param int signal: The integer signal to send to the process, e.g. ``process.signal(signal.SIGTERM)``.
		@raise pysys.exceptions.ProcessError: Raised if an error occurred whilst trying to signal the process
		"""
		log.info('Sending signal %s to process %s', signal, self)
		try:
			os.kill(self.pid, signal)
		except Exception:
			raise ProcessError("Error sending signal %s to process %r"%(signal, self))


	def write(self, data, addNewLine=True, closeStdinAfterWrite=False):
		"""Write binary data to the stdin of the process.
		
		Note that when the addNewLine argument is set to true, if a new line does not 
		terminate the input data string, a newline character will be added. If one 
		already exists a new line character will not be added. Should you explicitly 
		require to add data without the method appending a new line charater set 
		addNewLine to false.
		
		:param bytes|str data: The data to write to the process stdin. 
			As only binary data can be written to a process stdin, 
			if a character string rather than a byte object is passed as the data,
			it will be automatically converted to a bytes object using the encoding 
			given by ``PREFERRED_ENCODING``. 
		:param bool addNewLine: True if a new line character is to be added to the end of 
			the data string
		:param bool closeStdinAfterWrite: If True, the stdin file handle will be closed after this write. 
			Added in v2.1. 
			
		
		"""
		if not self.running(): raise Exception('Cannot write to process stdin when it is not running')
		
		if data is None: return
		if type(data) != binary_type:
			data = data.encode(PREFERRED_ENCODING)
		if addNewLine and not data.endswith(b'\n'): data = data+b'\n'
			
		if self._outQueue == None:
			# start thread on demand
			self._outQueue = Queue.Queue()
			
			__parentLogHandlers = pysysLogHandler.getLogHandlersForCurrentThread()
			def writeStdinThread():
				pysysLogHandler.setLogHandlersForCurrentThread(__parentLogHandlers)
				try:
					while self._outQueue:
						try:
							data = self._outQueue.get(block=True, timeout=0.25)
						except Queue.Empty:
							if not self.running(): 
								# no need to close stdin here, as previous call's setExitCode() method will do it
								break
						else:
							try:
								self._writeStdin(data)
							except Exception as ex:
								(log.debug if not self.running() else log.error)('Failed to write %r to stdin of process %r', data, self, exc_info=True)
				finally:
					pysysLogHandler.setLogHandlersForCurrentThread([])
			
			t = threading.Thread(target=writeStdinThread, name='pysys.stdinreader_%s'%str(self), daemon=True)
			t.start()
			
		if data: self._outQueue.put(data)
		if closeStdinAfterWrite: self._outQueue.put(None) # None is a sentinel value for EOF
		
	def running(self):
		"""Check to see if a process is running.
		
		:return: True if the process is currently running, False if not. 
		
		"""
		# check for pid=None in case start() got interrupted
		return self.pid is not None and self.setExitStatus() is None

	def wait(self, timeout):
		"""Wait for a process to complete execution, raising an exception on timeout.
		
		Logs and info message if the process takes more than a few seconds to complete. 

		This method provides basic functionality but does not check the exit status or log any messages; 
		see `pysys.basetest.BaseTest.waitProcess` for a wrapper that adds additional functionality. 
		
		Note that this method will not terminate the process if the timeout is exceeded. 
		
		:param timeout: The timeout to wait in seconds, for example ``timeout=TIMEOUTS['WaitForProcess']``.
		:raise pysys.exceptions.ProcessTimeout: Raised if the timeout is exceeded.
		
		"""
		assert timeout > 0, 'timeout must always be specified'
		startTime = time.monotonic()
		log.debug("Waiting up to %d secs for process %r", timeout, self)

		doneLongWaitLogging = False

		while self.running():
			currentTime = time.monotonic()
			if currentTime > startTime + timeout:
				raise ProcessTimeout('Waiting for completion of %r timed out after %d seconds'%(self, int(timeout)))
			self._pollWaitUnlessProcessTerminated()
			if doneLongWaitLogging is False and time.monotonic()-startTime>4:
				log.info("Waiting up to %d secs for process %r", timeout, self) # probably would be confusing to adjust this timeout based on time already waited
				doneLongWaitLogging = True
		
	def _pollWaitUnlessProcessTerminated(self):
		# Performs a short wait, but if the OS support it (e.g. Windows), abort waiting if the process is terminated
		self._pollWait(0.05)

	def start(self):
		"""Start a process using the runtime parameters set at instantiation.
		
		@raise pysys.exceptions.ProcessError: Raised if there is an error creating the process
		@raise pysys.exceptions.ProcessTimeout: Raised in the process timed out (foreground process only)
		
		"""
		self._outQueue = None # always reset
		
		if self.workingDir and not os.path.isdir(self.workingDir):
			raise Exception('Cannot start process %s as workingDir "%s" does not exist'% (self, self.workingDir))
		
		# unless we're performing some cleanup logic, don't permit new processes to begin after we've been told to shutdown
		if self.owner is not None and self.owner.isRunnerAborting is True and self.owner.isCleanupInProgress is False: raise KeyboardInterrupt()

		if self.state == FOREGROUND:
			self.startBackgroundProcess()
			self.wait(self.timeout)
		else:
			self.startBackgroundProcess()
