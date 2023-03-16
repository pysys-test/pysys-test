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
Contains operating system helper utilities such as the `getUsableCPUCount` function. 

"""

import sys, os
import threading
import logging
import time
import traceback
import math
import logging

from pysys.constants import *

__all__ = ['getUsableCPUCount']


__USABLE_CPU_COUNT = None

def getUsableCPUCount() -> float:
	"""
	The number of CPUs that are usable from this PySys process, as a floating point number. 

	This may be less than the total number of CPUs due to restrictions from the operating system 
	such as the process affinity mask and container cgroup (``cpu.cfs_quota_us`` / ``cpu.max``) limits. 

	.. versionadded:: 2.2
	"""
	if __USABLE_CPU_COUNT: return __USABLE_CPU_COUNT
	return _initUsableCPUCount()
	

def _initUsableCPUCount():
	""" Internal, do not use. 

	Called after importing BaseRunner (not when this module is imported) so that it's possible to monkey-patch 
	it in user code (e.g. when the custom runner is imported) if required e.g. for a new platform. 

	:meta private: Not public API
	"""
	log = logging.getLogger('pysys.initUsableCPUCount')

	global __USABLE_CPU_COUNT
	if __USABLE_CPU_COUNT:
		log.debug('Calling _initUsableCPUCount when it was previously called and returned %s', __USABLE_CPU_COUNT)

	try:
		cpus = len(os.sched_getaffinity(0)) # as recommended in Python docs, use the allocated CPUs for current process multiprocessing.cpu_count()
	except Exception: # no always available, e.g. on Windows
		cpus = os.cpu_count()
	assert cpus, cpus

	if (not IS_WINDOWS) and os.getenv('PYSYS_IGNORE_CGROUPS','').lower()!='true' and os.path.exists('/proc/self/cgroup'): 
		# if https://github.com/python/cpython/issues/80235 is implemented we can defer to Python to calculate this
	
		cgroupslog = logging.getLogger('pysys.cgroups')
		cgroups = CgroupConfig()

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
			reducedCPUs = min(cgroupsLimits) # use whatever limit is lowest
			if reducedCPUs<=0: reducedCPUs = 1 # should not happen, just a failsafe in case of weird cgroup config
			if reducedCPUs<cpus:
				cgroupslog.info('Reduced usable CPU count from %s to %s due to Cgroups configuration', cpus, reducedCPUs)
			cpus = reducedCPUs
		except Exception as ex:
			cgroupslog.info('Failed to read cgroups configuration to determine available CPUs: %r', ex) # 
			cgroupslog.debug('Failed to read cgroups information due to:', exc_info=True)

	log.debug('Usable CPU count for process = %d', cpus)

	__USABLE_CPU_COUNT = cpus
	return cpus


class CgroupConfig:
	"""
	Helper class for reading cgroups configuration for the current process, supporting both cgroups v1 and v2. 
	
	This is a minimal implementation, and assumes the  mount point is "/sys/fs/cgroup". Consider using a dedicated 
	library if you need something more advanced. 
	
	:meta private: This API is not yet stable enough for general use, and may change at any time. 

	"""
	def __init__(self, mountRoot=None):
		self.pid = 'self'
		self.controllers = {}
		""" Maps a controller name (in v1, or "" for v2) to the full path of that controller. """

		self.mountRoot = mountRoot or os.getenv('PYSYS_CGROUPS_ROOT_MOUNT', '/sys/fs/cgroup') # Would be more correct to look this up from /proc/self/mountinfo, but probably not necessary as almost everyone has it mounted in the standard location
		if IS_WINDOWS:
			self.mountRoot = None
		elif not os.path.exists(self.mountRoot):
			self._debuglog('No cgroup root is mounted at %s', mountRoot)
			self.mountRoot = None
	
	def __getControllerDir(self, cgroupsv1Controller):
		if not self.mountRoot: return None
		d = mountRoot = self.mountRoot
		
		if cgroupsv1Controller: 
			d = d+'/'+cgroupsv1Controller
		elif not os.path.exists(mountRoot+'/cgroup.controllers'):
			return None # can't be cgroups v2 if there is no controllers file
		
		with open('/proc/'+self.pid+'/cgroup') as f: # should always exist
			# Get the PATH from a matching HIERARCHY:CONTROLLER_LIST:PATH line, where CONTROLLER_LIST is a comma-separated list
			m = re.search(r'\d+:%s:(.*)'%('' if not cgroupsv1Controller else "([^:]+,)?"+cgroupsv1Controller+"(,[^:]+)?"), f.read())
		if not m: return None # return and log nothing if the relevant cgroup
		cgroup_path = m.groups()[-1].rstrip('/') # if it's "/" convert to ""
		
		if os.path.exists(d+cgroup_path): 
			d = d+cgroup_path
			self._debuglog('Reading cgroup configuration for %s controller from "%s" as given by /proc/self/cgroup file', 
		  		cgroupsv1Controller or '<cgroup v2>', d)
		else:
			# seems to often not exist in docker containers, as it's a path in the docker host that the container can't see
			self._debuglog('Reading cgroup configuration for %s controller from root dir "%s" since the path "%s" given by /proc/self/cgroup file was not found under the root dir',
		 	 	cgroupsv1Controller or '<cgroup v2>',  d, cgroup_path)
		
		return d

	def readFile(self, filename, v1Controller=None):
		"""
		Return as a string the first line of the specified cgroups filename belonging to the specified controller (always "" for cgroups v2). 
		
		:param str filename: The base filename within the controller, e.g. "cpu.max"
		:param str v1controller: To read cgroups v2 this should be None, for cgroups v1 this is the controller name, e.g. "cpu". 
		:return: A string containing the first line of the specified cgroups file, or empty string '' if the file or controller is missing. 
		"""
		v1Controller = v1Controller or ''
		assert ',' not in v1Controller, v1Controller
		if v1Controller not in self.controllers: # cache this where possible
			self.controllers[v1Controller] = self.__getControllerDir(v1Controller)
		dirname = self.controllers[v1Controller]
		
		if dirname and os.path.exists(dirname+'/'+filename):
			with open(dirname+'/'+filename) as f:
				return f.readline().strip()
		
		return ''
	
	def _debuglog(self, msg, *args): logging.getLogger('pysys.cgroups').debug(msg, *args)
