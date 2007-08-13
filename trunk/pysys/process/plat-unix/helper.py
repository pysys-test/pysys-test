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

import signal, time, copy, logging

from pysys.constants import *
from pysys.exceptions import *

# create the class logger
log = logging.getLogger('pysys.process.helper')


class ProcessWrapper:
	
	def __init__(self, command, arguments, environs, workingDir, state, timeout, stdout=None, stderr=None):
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
		self.stdin = None

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", self.stdout)
		log.debug("  stdout       : %s", self.stderr)
		#for e in self.environs.keys(): log.debug("  environment  : %s=%s", e, environs[e])
		

	def startBackgroundProcess(self):
		try:
			self.pid = os.fork()
			if self.pid == 0:
				new_stdout = os.open(self.stdout, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
				new_stderr = os.open(self.stderr, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
				os.dup2(new_stdout, 1)
				os.dup2(new_stderr, 2)

				arguments = copy.copy(self.arguments)
				arguments.insert(0, os.path.basename(self.command))
				os.execve(self.command, arguments, self.environs)
		except:
			if self.pid == 0: os._exit(os.EX_OSERR)	

		if not self.running() and self.exitStatus == os.EX_OSERR:
			raise ProcessError, "Error creating process %s" % (self.command)


	def startForegroundProcess(self):
		self.startBackgroundProcess()
		
		startTime = time.time()
		while self.running():
			if self.timeout:
				currentTime = time.time()
				if currentTime > startTime + self.timeout:
					self.stop()
					raise ProcessTimeout, "Process timedout"
			time.sleep(0.1)


	def setExitStatus(self):
		if self.exitStatus != None: return
		
		pid, status = os.waitpid(self.pid, os.WNOHANG)
		if pid == self.pid:
			if os.WIFEXITED(status):
				self.exitStatus = os.WEXITSTATUS(status)
			elif os.WIFSIGNALED(status):
				self.exitStatus = os.WTERMSIG(status)
			else:
				self.exitStatus = status


	def running(self):
		self.setExitStatus()
		if self.exitStatus != None: return 0
		return 1


	def stop(self):
		try:
			os.kill(self.pid, signal.SIGTERM)
			self.setExitStatus()
		except:
			raise ProcessError, "Error stopping process"


	def signal(self, signal):
		try:
			os.kill(self.pid, signal)
		except:
			raise ProcessError, "Error signaling process"


	def start(self):
		oldcwd = os.getcwd()
		os.chdir(self.workingDir)

		try:
			if self.state == FOREGROUND:
				self.startForegroundProcess()
			else:
				self.startBackgroundProcess()
		finally:
			os.chdir(oldcwd)





