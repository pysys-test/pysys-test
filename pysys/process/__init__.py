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
	:ivar int ~.exitStatus: The process exit status for a completed process (for many processes 0 represents success), 
		or None if it has not yet completed. 
	:ivar dict[str,obj] ~.info: A mutable dictionary of user-supplied information that was passed into startProcess, 
		for example port numbers, log file paths etc. 
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None, 
		expectedExitStatus=None, info={}):
		
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
		for e in keys: 
			value = self.environs[e]
			debuginfo.append("  environment  : %s=%s"%( e, value) )
			if 'PATH' in e.upper() and e.upper() not in ['PATHEXT']:
				# it's worth paths/classpaths/pythonpaths as they're often long and quite hard to spot differences otherwise
				pathelements = value.split(';' if ';' in value else os.pathsep)
				if len(pathelements)>1:
					for i, pathelement in enumerate(pathelements):
						#                         : ABC=def
						debuginfo.append("                   #%-2d %s"%( i+1, pathelement))
				
		if info: debuginfo.append("  info         : %s"% info)

		log.debug("Process parameters for %s\n%s", self, '\n'.join(d for d in debuginfo))

		# private
		self._outQueue = None


	def __str__(self): return self.displayName
	def __repr__(self): return '%s (pid %s)'%(self.displayName, self.pid)

	# these abstract methods must be implemented by subclasses; no need to publically document
	def setExitStatus(self): raise Exception('Not implemented')
	def startBackgroundProcess(self): raise Exception('Not implemented')
	def writeStdin(self): raise Exception('Not implemented')
	def stop(self): 
		"""Stop a running process.
		
		Does nothing if the process is not running. 
		
		@raise pysys.exceptions.ProcessError: Raised if an error occurred whilst trying to stop the process.		
		"""
		raise Exception('Not implemented')
		
	def signal(self, signal): 
		"""Send a signal to a running process. 
	
		Typically this uses ``os.kill`` to send the signal. 
	
		:param int signal: The integer signal to send to the process, e.g. ``process.signal(signal.SIGTERM)``.
		@raise pysys.exceptions.ProcessError: Raised if an error occurred whilst trying to signal the process
		"""
		try:
			os.kill(self.pid, signal)
		except Exception:
			raise ProcessError("Error sending signal %s to process %r"%(signal, self))


	def write(self, data, addNewLine=True):
		"""Write binary data to the stdin of the process.
		
		Note that when the addNewLine argument is set to true, if a new line does not 
		terminate the input data string, a newline character will be added. If one 
		already exists a new line character will not be added. Should you explicitly 
		require to add data without the method appending a new line charater set 
		addNewLine to false.
		
		:param data: The data to write to the process stdin. 
			As only binary data can be written to a process stdin, 
			if a character string rather than a byte object is passed as the data,
			it will be automatically converted to a bytes object using the encoding 
			given by ``PREFERRED_ENCODING``. 
		:param addNewLine: True if a new line character is to be added to the end of 
			the data string
		
		"""
		if not self.running(): raise Exception('Cannot write to process stdin when it is not running')
		
		if not data: return
		if type(data) != binary_type:
			data = data.encode(PREFERRED_ENCODING)
		if addNewLine and not data.endswith(b'\n'): data = data+b'\n'
			
		if self._outQueue == None:
			# start thread on demand
			self._outQueue = Queue.Queue()
			t = threading.Thread(target=self.writeStdin, name='pysys.stdinreader_%s'%str(self))
			t.start()
			
		self._outQueue.put(data)
		
	def running(self):
		"""Check to see if a process is running.
		
		:return: True if the process is currently running, False if not. 
		
		"""
		return self.setExitStatus() is None

	def wait(self, timeout):
		"""Wait for a process to complete execution, raising an exception on timeout.
		
		This method provides basic functionality but does not check the exit status or log any messages; 
		see `pysys.basetest.BaseTest.waitProcess` for a wrapper that adds additional functionality. 
		
		Note that this method will not terminate the process if the timeout is exceeded. 
		
		:param timeout: The timeout to wait in seconds, for example ``timeout=TIMEOUTS['WaitForProcess']``.
		:raise pysys.exceptions.ProcessTimeout: Raised if the timeout is exceeded.
		
		"""
		assert timeout > 0, 'timeout must always be specified'
		startTime = time.time()
		log.debug("Waiting up to %d secs for process %r", timeout, self)
		while self.running():
			currentTime = time.time()
			if currentTime > startTime + timeout:
				raise ProcessTimeout('Waiting for completion of %s timed out after %d seconds'%(self, int(timeout)))
			time.sleep(0.05)
		


	def start(self):
		"""Start a process using the runtime parameters set at instantiation.
		
		@raise pysys.exceptions.ProcessError: Raised if there is an error creating the process
		@raise pysys.exceptions.ProcessTimeout: Raised in the process timed out (foreground process only)
		
		"""
		self._outQueue = None # always reset
		
		if self.workingDir and not os.path.isdir(self.workingDir):
			raise Exception('Cannot start process %s as workingDir "%s" does not exist'% (self, self.workingDir))
		
		if self.state == FOREGROUND:
			self.startBackgroundProcess()
			self.wait(self.timeout)
		else:
			self.startBackgroundProcess()
