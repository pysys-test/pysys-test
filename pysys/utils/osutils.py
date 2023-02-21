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
Contains operating system helper utilities such as the `Cgroups` class. 

:meta private: This API is not yet stable enough for general use, and may change at any time. 

"""

import sys, os
import threading
import logging
import time
import traceback
import math
import logging

from pysys.constants import *

__all__ = ['CGroups']

class Cgroups:
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
			m = re.search(r'\d+:%s:(.*)'%('' if not cgroupsv1Controller else "([^:]+,)?"+cgroupsv1Controller+"(,[^:]+)?"), 
									f.readline())
		if not m: return None # return and log nothing if the relevant cgroup
		cgroup_path = m.groups()[-1].rstrip('/') # if it's "/" convert to ""
		
		if os.path.exists(d+cgroup_path): 
			d = d+cgroup_path
			self._debuglog('Reading cgroup configuration from "%s" as given by /proc/self/cgroup file', d)
		else:
			# seems to often not exist in docker containers, as it's a path in the docker host that the container can't see
			self._debuglog('Reading cgroup configuration from root dir "%s" since the path "%s" given by /proc/self/cgroup file was not found under the root dir', d, cgroup_path)
		
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
