#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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
import subprocess

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
			if self._stopping.is_set(): raise Exception('Requested to stop')

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
	
	Equivalent to running the `ps` command reading columns `pcpu`, `rss` and `vsz`, but 
	implemented directly since ps is not always installed. 
	"""
	def _getData(self, sample):
		with process_lock:
			proc_dir = f"/proc/{self.pid}"
			try:
				with open(os.path.join(proc_dir, "stat"), "r") as f:
					stat_fields = f.read().split()
				with open(os.path.join(proc_dir, "status"), "r") as f:
					status_lines = f.readlines()
			except FileNotFoundError:
				raise Exception(f"Process {self.pid} not found in /proc; perhaps it has terminated")
			except Exception as e:
				raise Exception(f"Error reading /proc for pid {self.pid}: {e}")

			# Calculate CPU usage
			cpu_usage = -1
			try:
				# Get clock ticks per second
				try:
					clk_tck = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
				except (AttributeError, KeyError, ValueError):
					clk_tck = 100  # fallback default

				# Defensive: Ensure stat_fields has enough fields
				if len(stat_fields) < 22:
					raise Exception(f"Unexpected /proc/{self.pid}/stat format: {stat_fields}")
				try:
					utime = int(stat_fields[13]) # user mode ticks
					stime = int(stat_fields[14]) # kernetl mode ticks
				except (IndexError, ValueError) as e:
					raise Exception(f"Error parsing stat fields for pid {self.pid}: {e}")

				cpu_ticks = utime + stime # user+kernel time
				now = time.monotonic()
				# Store previous values to calculate CPU usage since last call
				if not hasattr(self, '_last_cpu_values'):
					self._last_cpu_values = {
						'cpu_ticks': cpu_ticks,
						'timestamp': now,
					}
					cpu_usage = 0 # it's unavoidable for the first sample to be 0 and we don't want to treat that as an error
				else:
					delta_time = now - self._last_cpu_values['timestamp']
					if delta_time > 0:
						cpu_usage = 100 * (((cpu_ticks - self._last_cpu_values['cpu_ticks']) / clk_tck) / delta_time)
					self._last_cpu_values['cpu_ticks'] = cpu_ticks
					self._last_cpu_values['timestamp'] = now
			except Exception:
				pass

			# Memory usage: VmRSS and VmSize from /proc/[pid]/status
			mem_res_kb = mem_virt_kb = -1
			for line in status_lines:
				if line.startswith("VmRSS:"):
					try:
						mem_res_kb = int(line.split()[1])
					except Exception: pass
				elif line.startswith("VmSize:"):
					try:
						mem_virt_kb = int(line.split()[1])
					except Exception: pass

			data = {}
			data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = int(cpu_usage)
			data[ProcessMonitorKey.MEMORY_RESIDENT_KB] = mem_res_kb
			data[ProcessMonitorKey.MEMORY_VIRTUAL_KB] = mem_virt_kb		
			
			return data
			
if PLATFORM=='win32':
	DEFAULT_PROCESS_MONITOR = WindowsProcessMonitor
	"""Specifies the default L{BaseProcessMonitor} subclass to be used for 
	monitoring OS-level process information on the current platform. """
else:
	DEFAULT_PROCESS_MONITOR = UnixProcessMonitor
