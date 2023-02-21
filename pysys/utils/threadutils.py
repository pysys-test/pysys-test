#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2023 M.B.Grieve

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
Contains the `BackgroundThread` class and other utilities for working with threads.
"""

import sys, os
import threading
import logging
import time
import traceback
import math
import logging
from pathlib import Path

from pysys.constants import *
from pysys.internal.initlogging import pysysLogHandler
from pysys.utils.filegrep import getmatches
import pysys.utils.osutils

__all__ = ['BackgroundThread', 'createThreadInitializer', 'USABLE_CPU_COUNT']

USABLE_CPU_COUNT: int = None
"""
The number of CPUs that are usable from this PySys process. 

This may be less than the total number of CPUs due to restrictions from the operating system 
such as the process affinity mask and container cgroups (``cpu.cfs_quota_us``) limits. 

.. versionadded:: 2.2
"""

def _initUsableCPUCount():
	""" Internal, do not use. 

	Called after importing BaseRunner (not when this module is imported) so that it's possible to monkey-patch 
	it in user code (e.g. when the custom runner is imported) if required e.g. for a new platform. 

	:meta private: Not public API
	"""
	global USABLE_CPU_COUNT
	assert USABLE_CPU_COUNT == None # only set this once

	log = logging.getLogger('pysys.initUsableCPUCount')

	try:
		cpus = len(os.sched_getaffinity(0)) # as recommended in Python docs, use the allocated CPUs for current process multiprocessing.cpu_count()
	except Exception: # no always available, e.g. on Windows
		cpus = os.cpu_count()
	assert cpus, cpus

	if (not IS_WINDOWS) and os.getenv('PYSYS_IGNORE_CGROUPS','').lower()!='true' and os.path.exists('/proc/self/cgroup'): 
		# if https://github.com/python/cpython/issues/80235 is implemented we can defer to Python to calculate this
	
		cgroupslog = logging.getLogger('pysys.cgroups')
		cgroups = pysys.utils.osutils.Cgroups()

		try:
			cfs_quota_us  = int(cgroups.readFile('cpu.cfs_quota_us', v1Controller='cpu') or '0')
			cfs_period_us = int(cgroups.readFile('cpu.cfs_period_us', v1Controller='cpu') or '0')
			shares        = int(cgroups.readFile('cpu.shares', v1Controller='cpu') or '0') # just for information
			cgroupsLimits = []
			if cfs_quota_us>0 and cfs_period_us>0: 
				cgroupsLimits.append(float(cfs_quota_us) / float(cfs_period_us)) # quota is per CPU, i.e. quota>period if multiple CPUs permitted

			cpuMax = cgroups.readFile('cpu.max', v1Controller=None).split(' ')
			if len(cpuMax)==2 and cpuMax[0].lower()!='max':
				cgroupsLimits.append(float(cpuMax[0]) / float(cpuMax[1])) # seems to work the same as the v1 quota and period
			
			# do NOT use cpu.shares as it's not possible to do reliably (e.g. cf https://bugs.openjdk.org/browse/JDK-8281181)
				
			cgroupsLimits.append(cpus) # don't ever use more than the total CPUs in the machine so add that to the list of limits
			cgroupslog.debug('Read cgroups configuration: v1 cpu.cfs_quota_us/cfs_period_us=%s/%s (ignored: cpu.shares=%s), v2 cpu.max=%s; limiting to min of: %s CPUs', 
				cfs_quota_us or '?', cfs_period_us or '?', shares or '?', 
				'/'.join(cpuMax) or '?', 
				cgroupsLimits)
			reducedCPUs = max(1, math.ceil(min(cgroupsLimits))) # use whatever limit is lowest, but don't go below 1
			if reducedCPUs<cpus:
				cgroupslog.info('Reduced usable CPU count from %s to %s due to Cgroups configuration', cpus, reducedCPUs)
			cpus = reducedCPUs
		except Exception as ex:
			cgroupslog.info('Failed to read cgroups configuration to determine available CPUs: %r', ex) # 
			cgroupslog.debug('Failed to read cgroups information due to:', exc_info=True)

	log.debug('Usable CPU count for process = %d', cpus)

	USABLE_CPU_COUNT = cpus
	return cpus

def createThreadInitializer(owner):
	"""
	Creates a no-args initializer function that should be called at the start of a new thread created outside the PySys 
	framework to configure logging and thread name for the specified test/runner owner. 
	
	This function is needed because if a new thread is created without PySys helper methods (such as 
	`pysys.basetest.BaseTest.startBackgroundThread`) then logging from that thread will not go to the test's run.log 
	output file which can make debugging quite difficult. 
	
	.. versionadded:: 2.2
	
	"""
	loghandlers = pysysLogHandler.getLogHandlersForCurrentThread()
	assert loghandlers, loghandlers

	def initializer():
			# inherit log handlers from parent, whatever they are
			pysysLogHandler.setLogHandlersForCurrentThread(loghandlers)
			
			thisthread = threading.current_thread()
			
			# try to avoid 
			log = logging.getLogger('pysys.thread')
			
			if not thisthread.name.startswith(str(owner)):
				thisthread.name = str(owner)+':'+thisthread.name
			log.debug('Initialized PySys background thread: %s'%thisthread.name)
	
	return initializer

class BackgroundThread(object):
	"""
	PySys wrapper for a background thread that can receive requests to 
	stop, and can send log output to the same place as the test's logging. 

	To create a background thread in your test, use `pysys.basetest.BaseTest.startBackgroundThread`.

	:ivar str ~.name: The name specified for this thread when it was created. 
	
	:ivar int ~.joinTimeoutSecs: The default timeout that will be used for joining 
		this thread. If not explicitly set this will be L{TIMEOUTS}C{['WaitForProcessStop']}.
	
	:ivar Exception ~.exception: The exception object raised by the thread if it has 
		terminated with an error, or None if not. 
	"""
	def __init__(self, owner, name, target, kwargsForTarget):
		assert name, 'Thread name must always be specified'

		self.log = logging.getLogger('pysys.thread') # do not put name/test into this, as loggers aren't GC'd so don't want to create an unbounded number
		self.name = name
		self.owner = owner # a BaseTest
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
		self.log.info('Starting background thread %s'%self)
		
		self.initializer = createThreadInitializer(owner)
	
	def __repr__(self): return 'BackgroundThread[%s]'%self.thread.name
	def __str__(self): return self.name # without owner identifier
	
	def isAlive(self):
		"""
		:return: True if this thread is still running. 
		:rtype: bool
		"""
		return self.thread.is_alive()
	
	def __run(self, **kwargs):
		try:
			self.initializer()
			self.log.debug('%r starting'%self)
			self.__target(**kwargs)
			self.log.debug('%r completed successfully'%self)
		except Exception as ex:
			if self.stopping.is_set():
				self.log.info('Background thread %s raised an exception while being stopped (ignoring) - %s: %s'%(self, ex.__class__.__name__, ex))
				return
			# this is probably the only place we can really get and show the stack trace
			self.log.exception('Background thread %s.%s failed - '%(self.owner, self))
			
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
		thread to terminate, call L{join} afterwards. Calling this repeatedly 
		has no effect. 
		
		:return: This instance, in case you wish to do fluent method chaining.  
		:rtype: L{BackgroundThread}
		"""
		self.log.debug('Stop() requested for background thread %s', self)
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
		
		:param timeout: The time in seconds to wait. Usually this should be 
			left at the default value of None which uses a default timeout 
			of L{constants.TIMEOUTS}C{['WaitForProcessStop']}. 
			Note that unlike Python's `Thread.join` method, infinite timeouts 
			are not supported. 
		
		:param abortOnError: Set to True if you wish this method to 
			immediately abort with an exception if the background thread times out 
			or raises an Exception. The default is False, which adds the failure 
			outcome but does not raise an exception. 
		"""
		outcomereported = self.__outcomeReported
		self.__outcomeReported = True # only do this once
		
		if not timeout: timeout = self.joinTimeoutSecs
		assert self.joinTimeoutSecs > 0, self.joinTimeoutSecs

		if self.thread.is_alive() or (not outcomereported):
			# only log it the first time
			self.log.info('Joining background thread %s'%self)
		starttime = time.time()
		
		# don't call thread.join for the entire time, since on windows that 
		# leaves no opportunity to detect keyboard interrupts
		if self.__kbdrInterrupt: raise self.__kbdrInterrupt # avoid repeatedly joining same thread
		while self.thread.is_alive() and time.time()-starttime < timeout:
			try:
				self.thread.join(1)
			except KeyboardInterrupt as ex: # pragma: no cover
				self.__kbdrInterrupt = ex
				raise
		
		timetaken = time.time()-starttime
		
		if self.thread.is_alive():
		
			if not outcomereported:
				self.owner.addOutcome(TIMEDOUT, 'Background thread %s is still running after waiting for allocated timeout period (%d secs)'%(
					self, timeout), abortOnError=abortOnError)
				try:
					self.log.warning('Stack of hanging thread %s: \n%s', str(self), 
						''.join(traceback.format_stack(sys._current_frames()[self.thread.ident])))
				except Exception as ex:
					self.log.debug('Failed to get stack of hanging thread: %s: %s', ex.__class__.__name__, ex)
			self.stop() # ensure it stops as quickly as possible

		elif self.exception is not None:
			if not outcomereported:
				self.owner.addOutcome(BLOCKED, 'Background thread %s failed with %s: %s'%(
					self, self.exception.__class__.__name__, self.exception), abortOnError=abortOnError)
		elif timetaken >10: # alert user only if it took a long time
			self.log.info('Joined background thread %s in %0.1f seconds', self, timetaken)

