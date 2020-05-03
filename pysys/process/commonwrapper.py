#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
Contains the `pysys.process.commonwrapper.CommonProcessWrapper` class that represents a process PySys has started. 
"""

import os.path, time, threading, sys, locale
import logging
if sys.version_info[0] == 2:
	import Queue
else:
	import queue as Queue

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.pycompat import *

def _stringToUnicode(s):
	""" Converts a unicode string or a utf-8 bit string into a unicode string. 
	@deprecated: for internal use only, will be removed in future. 
	"""
	if not PY2: return s
	if isinstance(s, unicode):
		return s
	else:
		return unicode(s, "utf8")

log = logging.getLogger('pysys.process')

class CommonProcessWrapper(object):
	"""Represents a process that PySys has started (or can start).
	
	Instances of this class are returned by `pysys.process.user.ProcessUser.startProcess` (it's usually not 
	helpful to create instances directly).
	
	:ivar str ~.command:  The full path to the executable.
	:ivar list[str] ~.arguments:  A list of arguments to the command.
	:ivar dict(str,str) ~.environs:  A dictionary of environment variables (key, value) for the process context execution. 
		Use unicode strings rather than byte strings if possible; on Python 2 byte strings are converted 
		automatically to unicode using utf-8. 
	:ivar str ~.workingDir:  The working directory for the process
	:ivar ~.state: The state of the process.
	:vartype state: `pysys.constants.FOREGROUND` or `pysys.constants.BACKGROUND`
	:ivar int ~.timeout:  The time in seconds for a foreground process to complete.
	:ivar str ~.stdout: The full path to the filename to write the stdout of the process, or None for no stderr stream.
	:ivar str ~.stderr: The full path to the filename to write the stderr of the process, or None for no stderr stream. 
	:ivar str ~.displayName: Display name for this process (defaults to the basename if not explicitly specified). The 
		display name is returned by calling ``str()`` on this instance. The display name and pid are returned by 
		``repr()``.

	:ivar int ~.pid: The process id for a running or complete process (as set by the OS), or None if it is not yet started.
	:ivar int ~.exitStatus: The process exit status for a completed process (for many processes 0 represents success), 
		or None if it has not yet completed. 
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None):
		self.displayName = displayName if displayName else os.path.basename(command)
		self.command = command
		self.arguments = arguments
		self.environs = {}
		for key in environs: self.environs[_stringToUnicode(key)] = _stringToUnicode(environs[key])
		self.workingDir = workingDir
		self.state = state
		self.timeout = timeout

		# 'publicly' available data attributes set on execution
		self.pid = None
		self.exitStatus = None
		
		# these may be further updated by the subclass
		self.stdout = stdout
		self.stderr = stderr

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", stdout)
		log.debug("  stderr       : %s", stderr)
		keys=list(self.environs.keys())
		keys.sort()
		for e in keys: log.debug("  environment  : %s=%s", e, self.environs[e])

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
			given by ``locale.getpreferredencoding()``. 
		:param addNewLine: True if a new line character is to be added to the end of 
			the data string
		
		"""
		if not self.running(): raise Exception('Cannot write to process stdin when it is not running')
		
		if not data: return
		if type(data) != binary_type:
			data = data.encode(locale.getpreferredencoding())
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
		"""Wait for a process to complete execution.
		
		The method will block until either the process is no longer running, or the timeout 
		is exceeded. Note that the method will not terminate the process if the timeout is 
		exceeded. 
		
		:param timeout: The timeout to wait in seconds. Always provide a 
			timeout, otherwise your test may block indefinitely!
		@raise pysys.exceptions.ProcessTimeout: Raised if the timeout is exceeded.
		
		"""
		startTime = time.time()
		while self.running():
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					raise ProcessTimeout("Process timedout")
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
