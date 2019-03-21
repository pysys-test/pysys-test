#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018 M.B.Grieve

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
Module containing the L{BackgroundThread} class.
"""

import sys, os
import threading
import logging
import time
from pysys.constants import *
from pysys.internal.initlogging import pysysLogHandler

__all__ = ['BackgroundThread']

class BackgroundThread(object):
	"""
	PySys wrapper for a background thread that can receive requests to 
	stop, and can send log output to the same place as the test's logging. 
	"""
	def __init__(self, owner, name, target, kwargsForTarget):
		"""
		For details see L{pysys.BaseTest.startBackgroundThread}.
		
		@param owner: The BaseTest that owns this background thread and is 
		responsible for ensuring it is terminated during cleanup. 
		"""
		assert name, 'Thread name must always be specified'

		self.log = logging.getLogger('pysys.thread.%s'%name) # name without the owner prefix
		self.owner = owner
		self.__parentLogHandlers = pysysLogHandler.getLogHandlersForCurrentThread()
		assert self.__parentLogHandlers, self.__parentLogHandlers
		self.__target = target
		self.stopping = threading.Event()
		self.joinTimeoutSecs = TIMEOUTS['WaitForProcessStop']
		self.exception = None

		kwargs = dict(kwargsForTarget) if kwargsForTarget is not None else {}
		kwargs['stopping'] = self.stopping
		kwargs['log'] = self.log
		self.thread = threading.Thread(name='%s.%s'%(str(owner), name), target=self.__run, kwargs=kwargs)
		self.thread.daemon = True
		
		# add an undocumented alias matching threading.Thread's
		self.is_alive = self.isAlive
		
		self.__outcomeReported = False
		self.__kbdrInterrupt = None
		self.log.info('Starting background thread %r'%self)
	
	def __repr__(self): return 'BackgroundThread[%s]'%self.thread.name
	def __str__(self): return self.name # without owner identifier
	
	def isAlive(self):
		"""
		@return: True if this thread is still running. 
		@rtype: bool
		"""
		return self.thread.isAlive()
	
	def __run(self, **kwargs):
		try:
			# inherit log handlers from parent, whatever they are
			pysysLogHandler.setLogHandlersForCurrentThread(self.__parentLogHandlers)
			self.log.debug('%r starting'%self)
			self.__target(**kwargs)
			self.log.debug('%r completed successfully'%self)
		except Exception as ex:
			if self.stopping.is_set():
				self.log.info('%r raised an exception while being stopped (ignoring) - %s: %s'%(self, ex.__class__.__name__, ex))
				return
			# this is probably the only place we can really get and show the stack trace
			self.log.exception('%r Background thread failed - '%self)
			
			# set this so we can report the BLOCKED outcome
			self.exception = ex
		finally:
			pysysLogHandler.flush()
			pysysLogHandler.setLogHandlersForCurrentThread([])

	def stop(self):
		"""
		Requests the thread to stop by setting the `stopping` event which 
		the thread ought to be checking regularly. 
		
		This method returns immediately; if you wish to wait for the 
		thread to terminate, call L{join} afterwards.
		
		@return: This instance, in case you wish to do fluent method chaining.  
		"""
		self.stopping.set()
		return self
		
	def join(self, timeout=None, abortOnError=False):
		"""
		Wait until this thread terminates, and adds a TIMEDOUT or BLOCKED 
		outcome to the owner test if it times out or raises an exception.
		
		If you wish to request the thread to terminate rather than waiting for 
		it to reach the end of its target function on its own, call L{stop} 
		before joining the thread. 
		
		If a join times out, the thread is automatically requested to stop 
		as soon as possible. 
		
		Note that if the thread raises an Exception after it was requested to 
		stop this is logged but does not result in a failure outcome, 
		since failures during cleanup are usually to be expected. 
		
		@param timeout: The time in seconds to wait. Usually this should be 
		left at the default value of None which uses a default timeout 
		of L{constants.TIMEOUTS}C{['WaitForProcessStop']}. 
		Note that unlike Python's `Thread.join` method, infinite timeouts 
		are not supported. 
		
		@param abortOnError: Set to True if you wish this method to raise an 
		exception if the thread times out or raises an Exception. 
		"""
		outcomereported = self.__outcomeReported
		self.__outcomeReported = True # only do this once
		
		if not timeout: timeout = self.joinTimeoutSecs
		assert self.joinTimeoutSecs > 0, self.joinTimeoutSecs

		if self.thread.isAlive() or (not outcomereported):
			# only log it the first time
			self.log.info('Joining background thread %r'%self)
		starttime = time.time()
		
		# don't call thread.join for the entire time, since on windows that 
		# leaves no opportunity to detect keyboard interrupts
		if self.__kbdrInterrupt: raise self.__kbdrInterrupt # avoid repeatedly joining same thread
		while self.thread.isAlive() and time.time()-starttime < timeout:
			try:
				self.thread.join(1)
			except KeyboardInterrupt as ex: # progra: no cover
				self.__kbdrInterrupt = ex
				raise
		
		if self.thread.isAlive():
			self.stop() # ensure it stops as quickly as possible
			if not outcomereported:
				# TODO: print stack trace for the thread
				self.owner.addOutcome(TIMEDOUT, 'Background thread %s is still running after waiting for allocated timeout period (%d secs)'%(
					self.thread.name, timeout), abortOnError=abortOnError)
		elif self.exception is not None:
			if not outcomereported:
				self.owner.addOutcome(BLOCKED, 'Background thread %s failed with %s: %s'%(
					self.thread.name, self.exception.__class__.__name__, self.exception), abortOnError=abortOnError)
		elif time.time()-starttime>1:
			self.log.info('Joined background thread %r in %0.1f seconds', self, (time.time()-starttime))