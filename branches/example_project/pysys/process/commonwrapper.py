#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

from pysys import log
from pysys import process_lock
from pysys.constants import *
from pysys.exceptions import *

# check for new lines on end of a string
EXPR = re.compile(".*\n$")

def _stringToUnicode(s):
	""" Converts a unicode string or a utf-8 bit string into a unicode string. 
	
	"""
	if isinstance(s, unicode):
		return s
	else:
		return unicode(s, "utf8")

class CommonProcessWrapper(object):
	"""Abstract base process wrapper class for process execution and management.
	
	A base implementation of common process related operations, which should be extended
	by the OS specific wrapper classes.

	@ivar pid: The process id for a running or complete process (as set by the OS)
	@type pid: integer
	@ivar exitStatus: The process exit status for a completed process	
	@type exitStatus: integer
	
	"""

	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None, displayName=None):
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

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", stdout)
		log.debug("  stderr       : %s", stderr)
		keys=self.environs.keys()
		keys.sort()
		for e in keys: log.debug("  environment  : %s=%s", e, self.environs[e])

		# private
		self._outQueue = None


	def __str__(self): return self.displayName
	def __repr__(self): return '%s (pid %s)'%(self.displayName, self.pid)

	# these abstract methods must be implemented by subclasses
	def setExitStatus(self): raise Exception('Not implemented')
	def startBackgroundProcess(self): raise Exception('Not implemented')
	def writeStdin(self): raise Exception('Not implemented')
	def stop(self): raise Exception('Not implemented')
	def signal(self): raise Exception('Not implemented')

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
		if not self.running(): raise Exception('Cannot write to process stdin when it is not running')
		if addNewLine and not EXPR.search(data): data = "%s\n" % data
			
		if self._outQueue == None:
			# start thread on demand
			self._outQueue = Queue.Queue()
			thread.start_new_thread(self.writeStdin, ())
			
		self._outQueue.put(data)
		
	def running(self):
		"""Check to see if a process is running, returning true if running.
		
		@return: The running status (True / False)
		@rtype: integer
		
		"""
		return self.setExitStatus() is None


	def wait(self, timeout):
		"""Wait for a process to complete execution.
		
		The method will block until either the process is no longer running, or the timeout 
		is exceeded. Note that the method will not terminate the process if the timeout is 
		exceeded. 
		
		@param timeout: The timeout to wait in seconds. Always provide a 
			timeout, otherwise your test may block indefinitely!
		@raise ProcessTimeout: Raised if the timeout is exceeded.
		
		"""
		startTime = time.time()
		while self.running():
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:
					raise ProcessTimeout, "Process timedout"
			time.sleep(0.05)
		


	def start(self):
		"""Start a process using the runtime parameters set at instantiation.
		
		@raise ProcessError: Raised if there is an error creating the process
		@raise ProcessTimeout: Raised in the process timed out (foreground process only)
		
		"""
		self._outQueue = None # always reset
		
		if self.workingDir and not os.path.isdir(self.workingDir):
			raise Exception('Cannot start process %s as workingDir "%s" does not exist'% (self, self.workingDir))
		
		if self.state == FOREGROUND:
			self.startBackgroundProcess()
			self.wait(self.timeout)
		else:
			self.startBackgroundProcess()
