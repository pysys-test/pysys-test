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

import string, os.path, time, thread, logging
import win32api, win32pdh, win32security, win32process, win32file, win32pipe, win32con, pywintypes

from pysys.constants import *
from pysys.exceptions import *

# create the class logger
log = logging.getLogger('pysys.process.helper')


class NullDevice:
	def write(self, s):
		pass

	def flush(self):
		pass
	

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

		# private instance variables
		self.__hProcess = None
		self.__hThread = None
		self.__tid = None

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
			log.info("Unable to create file to capture stdout - usingthe null device")

		# print process debug information
		log.debug("Process parameters for executable %s" % os.path.basename(self.command))
		log.debug("  command      : %s", self.command)
		for a in self.arguments: log.debug("  argument     : %s", a)
		log.debug("  working dir  : %s", self.workingDir)
		log.debug("  stdout       : %s", self.stdout)
		log.debug("  stdout       : %s", self.stderr)
		#for e in self.environs.keys(): log.debug("  environment  : %s=%s", e, environs[e])


	def collectStdout(self, hStdout, fStdout):	
		buffer = win32file.AllocateReadBuffer(200)
		while 1:
			try:
				res, str = win32file.ReadFile(hStdout, buffer)
				if res == 0:
					str = string.replace(str, "\r\n", "\n")
					self.fStdout.write(str)
			except:
				if not self.running(): break


	def collectStderr(self, hStderr, fStderr):
		buffer = win32file.AllocateReadBuffer(200)
		while 1:
			try:
				res, str = win32file.ReadFile(hStderr, buffer)
		  		if res == 0: 
				  	str = string.replace(str, "\r\n", "\n")
					fStderr.write(str)
			except:
				if not self.running(): break


	def quotePath(self, input):
		i = input
		if i.find(' ') > 0:
			return '\"%s\"' % i
		else:
			return i


	def startBackgroundProcess(self):
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
		old_command = command = self.quotePath(self.command)
		for arg in self.arguments: command = '%s %s' % (command, self.quotePath(arg))
		try:
			self.__hProcess, self.__hThread, self.pid, self.__tid = win32process.CreateProcess( None, command, None, None, 1, 0, self.environs, os.path.normpath(self.workingDir), StartupInfo)
		except pywintypes.error:
			raise ProcessError, "Error creating process %s" % (old_command)

		win32file.CloseHandle(hStdin_r)
		win32file.CloseHandle(hStdout_w)
		win32file.CloseHandle(hStderr_w)

		# check to see if the process is running. If it is kick off the threads to collect
		# the stdout and stderr
		if self.running():					
			thread.start_new_thread(self.collectStdout, (hStdout, self.fStdout))
			thread.start_new_thread(self.collectStderr, (hStderr, self.fStderr))


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
		exitStatus = win32process.GetExitCodeProcess(self.__hProcess)
		if exitStatus != win32con.STILL_ACTIVE:
			self.exitStatus = exitStatus


	def running(self):
		self.setExitStatus()
		if self.exitStatus != None: return 0
		return 1


	def stop(self): 
		if self.exitStatus !=None: return 
		try:
			win32api.TerminateProcess(self.__hProcess,0)
			self.setExitStatus()
		except:
			raise ProcessError, "Error stopping process"


	def signal(self):
		raise NotImplementedError , "Unable to send a signal to a windows process"


	def start(self):
		if self.state == FOREGROUND:
			self.startForegroundProcess()
		else:
			self.startBackgroundProcess()
			time.sleep(1)




					   
