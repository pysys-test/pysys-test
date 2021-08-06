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
Contains implementations of the L{pysys.process.monitor.BaseProcessMonitor} interface. 
"""

__all__ = ['DEFAULT_PROCESS_MONITOR', 'WindowsProcessMonitor', 'UnixProcessMonitor']


import os, sys, string, time, logging
from pysys import process_lock
from pysys.constants import *
from pysys.utils.pycompat import *
from pysys.process.monitor import *

if PLATFORM=='win32' and 'sphinx' not in sys.modules:
	import win32api, win32pdh, win32con, win32process

log = logging.getLogger('pysys.processmonitor')

class WindowsProcessMonitor(BaseProcessMonitor):
	"""
	Windows implementation of a process monitor. 
	
	Uses the `GetProcessMemoryInfo`, and `GetProcessTimes` APIs. 
	The UserTime and KernelTime are summed together to calculate the CPU 
	utilization for this process. 
	"""
	
	def start(self):
		self._hPid = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION, 0, self.pid)
		self._lastValues = None

		return BaseProcessMonitor.start(self)

	def _timer_ns(self):
		""" Return a monotonically incrementing clock value in nanoseconds (1000**3) that 
		can be used to calculate performance results. 
		"""
		return win32api.GetTickCount()*1000000 # millis->nanos.

	def _cleanup(self):
		self._hPid.close()

	def _getData(self, sample):
		while True: # loop until we have both a "new" and a "last" value for CPU time
			if self._stopping.isSet(): raise Exception('Requested to stop')

			newvalues = {}
			newvalues['time_ns'] = self._timer_ns()
			cputimes = win32process.GetProcessTimes(self._hPid)
			newvalues['cputime_ns'] = (cputimes['KernelTime']+cputimes['UserTime'])*100 # convert to ns; comes in 100*ns units

			if self._lastValues is not None:
				if newvalues['time_ns']-self._lastValues['time_ns'] <= 0:
					# wait a bit longer to avoid div by zero error if the sleeping is somehow messed up
					self._stopping.wait(min(self.interval, 1))
					continue
			
				lastvalues = self._lastValues
				break
			
			# this is just for the first time _getData is called; need to repeat this once so we have stats to compare to
			self._lastValues = lastvalues = newvalues
			self._stopping.wait(min(self.interval, 1))
		
		memInfo = win32process.GetProcessMemoryInfo(self._hPid)
		
		data = {}

		# multiply by 100 to get utilization as a %
		data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = (100*(newvalues['cputime_ns']-lastvalues['cputime_ns']))//(newvalues['time_ns']-lastvalues['time_ns'])

		self._lastValues = newvalues
		
		data[ProcessMonitorKey.MEMORY_RESIDENT_KB] = memInfo['WorkingSetSize']//1024
		data[ProcessMonitorKey.MEMORY_VIRTUAL_KB] = memInfo['PagefileUsage']//1024
		
		return data

class UnixProcessMonitor(BaseProcessMonitor):
	"""
	Unix implementation of a process monitor. 
	
	Uses the `ps` command line tool, reading columns `pcpu`, `rss` and `vsz`. 
	"""
	def _getData(self, sample):
		with process_lock:
			with os.popen("ps -p %d -o pid,pcpu,rss,vsz"%self.pid) as fp: 
				info = fp.readlines()
			
			if len(info) <= 1: raise Exception('No matching processes found from ps; perhaps process has terminated')
			assert len(info) == 2, 'Unexpected ps output: %s'%info
			thisdata = info[1].split()
			data = {}
			data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = int(float(thisdata[1]))
			data[ProcessMonitorKey.MEMORY_RESIDENT_KB] = int(float(thisdata[2]))
			data[ProcessMonitorKey.MEMORY_VIRTUAL_KB] = int(float(thisdata[3]))
			
			return data
			
if PLATFORM=='win32':
	DEFAULT_PROCESS_MONITOR = WindowsProcessMonitor
	"""Specifies the default L{BaseProcessMonitor} subclass to be used for 
	monitoring OS-level process information on the current platform. """
else:
	DEFAULT_PROCESS_MONITOR = UnixProcessMonitor
