#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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

from __future__ import print_function

__all__ = ['BaseProcessMonitorHandler', 'BaseProcessMonitorHandler', 'TabSeparatedFileHandler', 'ProcessMonitorKey', 
	'ProcessMonitor', 'WindowsProcessMonitor', 'LinuxProcessMonitor', 'SolarisProcessMonitor']

"""
Contains the L{BaseProcessMonitor}, L{ProcessMonitorKey} constants for identifying 
columns and the default L{TabSeparatedFileHandler} class for writing monitoring 
information to a file. 
"""


import os, sys, string, time, threading, logging, multiprocessing
from pysys import process_lock
from pysys.constants import *
from pysys.utils.pycompat import *


if PLATFORM=='win32' and 'epydoc' not in sys.modules:
	import win32api, win32pdh

log = logging.getLogger('pysys.processmonitor')

class ProcessMonitorKey(object):
	"""
	Contains constants for supported process monitor keys. 
	
	Some of these keys are not currently returned on all platforms. 
	
	These constants provide the display names used for column headings etc. 
	
	Usually L{CPU_CORE_UTILIZATION} is the best key for measuring 
	CPU utilization and L{MEMORY_RESIDENT_KB} is the most useful way to 
	monitor memory usage. 
	"""

	CPU_CORE_UTILIZATION = 'CPU core %'
	"""CPU utilization % scaled by the number of cores so that 100% indicates 
	full use of one core, 200% indicates full use of two cores, etc. 
	
	The maximum value is 100 multiplied by the number of CPU cores 
	(as given by `multiprocessing.cpu_count()`). 
	"""

	CPU_TOTAL_UTILIZATION = 'CPU total %'
	"""Total utilization % of all available CPU cores, with a maximum value of 100%.
	
	If you have 2 cores and one of them is 50% utilized, the value would be 25%.
	"""
	
	MEMORY_RESIDENT_KB = 'Resident memory kB'
	"""
	Resident / working set memory usage. 
	
	This is usually a good way to check for memory leaks and excessive 
	memory usage. 

	Equivalent to `rss` on Unix; 
	on Windows calculated from the `Working Set` performance counter. 

	"""
	
	MEMORY_VIRTUAL_KB = 'Virtual memory kB'
	"""
	Virtual memory / address space of the process. This can be significant larger than 
	the amount actually allocated. 
	
	Equivalent to `vsz` on Unix; 
	on Windows calculated from the `Virtual Bytes` performance counter. 
	"""
	
	MEMORY_PRIVATE_KB = 'Private memory kB'
	"""
	Memory allocated to this process that cannot be shared with other processes. Windows only. 

	Calculated from the `Private Bytes` performance counter. 
	"""
	
	THREADS = 'Threads'
	"""
	Total number of threads for this process. 
	
	Not available on all operating systems. 
	"""
	
	KERNEL_HANDLES = 'Kernel handles'
	"""
	Total number of open kernel object handles. Windows-only.
	
	Corresponds to the 'Handle Count' performance counter. 
	"""
	
	DATE_TIME = 'Time'
	"""String representation of the date and local time for this sample 
	in yyyy-mm-dd HH:MM:SS format. 
	"""

	DATE_TIME_LEGACY = 'Time (legacy)'
	"""String representation of the date and local time for this sample in 
	a format compatible with older versions of PySys. 
	
	This is %d/%m/%y %H:%M:%S on Windows and %m/%d/%y %H:%M:%S on Unix. 
	@deprecated: Use L{DATE_TIME} if possible. 
	"""
	
	SAMPLE = 'Sample'
	"""A counter starting from 1 and incrementing with each new set of 
	sample data."""
	

class BaseProcessMonitorHandler(object):
	"""
	Interface to be implemented to provide a custom handler that records 
	or processes data from a L{BaseProcessMonitor}. 
	"""
	def handleData(self, data, **kwargs):
		"""
		Called on a background thread each time a new sample of monitoring 
		data is available. 
		
		@param data: a dictionary whose keys are from L{ProcessMonitorKeys} 
		and values are int, float or string values. 
		
		@param kwargs: Reserved for future use. 
		"""
		raise NotImplementedError('Not implemented yet')
	
	def cleanup(self):
		"""
		Called on a background thread to perform cleanup for this handler, 
		for example closing file handles. 
		"""
		pass

class TabSeparatedFileHandler(BaseProcessMonitorHandler):
	"""A ProcessMonitor handler that writes values to a file with 
	tab separated values (.tsv). 
	
	A new line is written every time the process monitor polls for a new sample 
	of data. By default a header line starting with `#` is included at the 
	start of the file to indicate the column headings. 
	
	If any value cannot be retrieved or is unavailable on this operating 
	system, a -1 value will be written instead. 
	"""
	
	DEFAULT_COLUMNS = [
		ProcessMonitorKey.DATE_TIME, 
		ProcessMonitorKey.CPU_CORE_UTILIZATION, 
		ProcessMonitorKey.MEMORY_RESIDENT_KB,
		ProcessMonitorKey.MEMORY_VIRTUAL_KB,
		]
	"""The default columns to write to the file.
	
	Additional columns may be added to the end of this list in future 
	releases. 
	
	See L{setDefaults} if you wish to change the defaults.
	"""
	
	DEFAULT_WRITE_HEADER_LINE = True
	"""
	Determines whether a header line prefixed 
	by `#` will be written at the start of the file.

	See L{setDefaults}.
	"""
	
	@staticmethod
	def setDefaults(columns, writeHeaderLine=None):
		"""Static helper method for setting the default columns or 
		writeHeaderLine setting for all tests that use the 
		TabSeparatedFileHandler. 
		
		This method could be called from a custom runner's 
		L{pysys.baserunner.BaseRunner.setup} method in order to take effect 
		for all tests. 
		
		Do not call this from within an individual testcase since that 
		could cause unwanted interference between different testcases. 
		
		@param columns: A list of the colums to be included, using values from
		L{ProcessMonitorKeys}. Since additional columns may be added to the end 
		of L{DEFAULT_COLUMNS} in future releases, when calling this method you 
		should specify all the columns you want explicitly including the 
		current defaults rather than writing `DEFAULT_COLUMNS+[...]`. 
		
		@param writeHeaderLine: Specifies whether a header line beginning 
		with `#` should be written at the start of the file. 
		"""
		if columns: TabSeparatedFileHandler.DEFAULT_COLUMNS = list(columns)
		if writeHeaderLine != None: TabSeparatedFileHandler.DEFAULT_WRITE_HEADER_LINE = writeHeaderLine
	
	def __init__(self, file, columns=None, writeHeaderLine=None):
		"""
		@param file: An absolute path string or open file handle to which 
		process monitor data lines will be written. 
		
		@param: An ordered list of the columns from L{ProcessMonitorKeys} that 
		should be included in the file. If not specifed, the columns specified 
		by L{DEFAULT_COLUMNS} will be used. 
		
		@param writeHeaderLine: Determines whether a header line prefixed 
		by `#` will be written at the start of the file. If not overridden, the 
		default is taken from L{DEFAULT_WRITE_HEADER_LINE}.
		"""
		self.columns = columns or self.DEFAULT_COLUMNS
		assert file, 'file must be specified'
		if isstring(file):
			assert os.path.isabs(file), 'File must be an absolute path: %s'%file
			self.stream = openfile(file, 'w', encoding='utf-8')
			self.__closeStream = True
		else:
			assert hasattr(file, 'write')
			self.stream = file
			self.__closeStream = False

		if writeHeaderLine is None: writeHeaderLine = self.DEFAULT_WRITE_HEADER_LINE
		if writeHeaderLine:
			self.stream.write(u'#%s\n'%u'\t'.join(self.columns).replace(u' ',u'_'))
		self.stream.flush()
	
	def handleData(self, data):
		values = [data.get(k,None) for k in self.columns]
		line = u'\t'.join([
			(str(d) if d is not None else u'-1')
			for d in values])
		self.stream.write(line)
		self.stream.write(u'\n')
		self.stream.flush()
	
	def cleanup(self):
		if self.__closeStream: self.stream.close()

class BaseProcessMonitor(object):
	"""Process monitor for gathering statistics such as CPU and memory usage 
	from a running process using a background thread. 
	
	For detail on the available statistic keys see L{ProcessMonitorKeys}.
	
	The most convenient way to start the default process monitor for this 
	operating system is to use L{pysys.basetest.BaseTest.startProcessMonitor}.
	
	You can create a custom subclass if you need to add support for a new OS 
	or return additional monitoring statistics.  

	The process monitor uses either the win32pdh module (on Windows) or the 
	`ps` command line utility (Unix systems) to obtain statistics on a given 
	process. Monitors are automatically terminated during cleanup at the end 
	of a test, or can be manually stopped before that using the L{stop} method. 
	"""
	
	def __init__(self, owner, process, interval, handlers, **pmargs):
		"""Construct an instance of the process monitor.
		
		@param owner: The BaseTest owning this monitor. 
		
		@param process: The process wrapper object. A numeric pid can be specified 
		instead but with reduced functionality, so use a process object if you 
		have one. 
		
		@param interval: The interval in seconds between polling for each data 
		sample. 
		
		@param pmargs: Keyword arguments to allow parameterization of the 
		returned data. An exception will be raised for any arguments not 
		expected by this class. 
		"""
		
		# NB: this could be subclassed to support different platforms and/or add extra 
		# data
		
		self.interval = interval
		
		# since 1.4.0 this is deprecated/undocumented, but keep it around 
		# for compatibility
		self.__numProcessors=1
		if "numProcessors" in pmargs: 
			self.__numProcessors = int(pmargs.pop("numProcessors"))
		
		assert not pmargs, 'Unknown process monitor options: %s'%pmargs.keys()

		self.process = None if isinstance(process, int) else process
		"""The process object. Can be None if a pid was passed directly. """

		self.pid = process if isinstance(process, int) else process.pid
		"""The pid to be monitored. """

		self.owner = owner
		"""The test object that owns this monitor. """
		
		assert handlers
		self.handlers = handlers
		"""The list of handlers that will be notified each time the process 
		is polled for new data. """
		
		self.thread = None
		"""
		The background thread that responsible for monitoring the process. 
		"""
		
		try:
			self._cpuCount = multiprocessing.cpu_count()
			"""The count of available CPU cores on this host, used 
			for scaling up the CPU_TOTAL_UTILIZATION. 
			"""
		except Exception as ex:
			log.debug('Failed to get multiprocessing.cpu_count: %s', ex)
			self._cpuCount = 1
		
	def start(self):
		"""
		Called on the main test thread to start monitoring in the background. 
		
		Performs any required initialization of data structures then 
		starts the background thread. 
		"""
		# executed on main thread - the best place to perform initial setup so we 
		# get an immediate error if it fails
		self.thread = self.owner.startBackgroundThread('ProcessMonitor<%s>'%('%s pid=%d'%(self.process,self.pid) if self.process else self.pid), self.__backgroundThread)
	
	def _preprocessData(self, data):
		""" Called in the background thread with the data dictionary from 
		each poll of the process, to allow OS-agnostic pre-processing and 
		addition of derived data keys such as the date and time. 
		
		@param data: The dictionary of process monitoring data. This method 
		may add or modify the contents of this dictionary. 
		
		"""
		
		datetime = time.gmtime(time.time())
		data[ProcessMonitorKey.DATE_TIME] = time.strftime("%Y-%m-%d %H:%M:%S", datetime)
		data[ProcessMonitorKey.DATE_TIME_LEGACY] = time.strftime(
			"%d/%m/%y %H:%M:%S" if IS_WINDOWS else "%m/%d/%y %H:%M:%S", datetime)
		
		if data.get(ProcessMonitorKey.CPU_CORE_UTILIZATION,None):

			data[ProcessMonitorKey.CPU_TOTAL_UTILIZATION] = int(data[ProcessMonitorKey.CPU_CORE_UTILIZATION] / self._cpuCount)
			
			if self.__numProcessors > 1:
				# undocumented, for compatibility only
				data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = data[ProcessMonitorKey.CPU_CORE_UTILIZATION] / self.__numProcessors
	
	def __backgroundThread(self, log, stopping):
		sample = 1
		try:
			while not stopping.is_set():
				d = self._getData(sample)
				assert d, 'No data returned'
				
				d[ProcessMonitorKey.SAMPLE] = sample
				self._preprocessData(d)
				
				for h in self.handlers:
					h.handleData(d)
				sample += 1
				stopping.wait(self.interval)
		except Exception as ex:
			if self.process and not self.process.running():
				log.debug('Ignoring process monitor error as the monitored process %s has already terminated: %s', self.process, ex)
			else:
				raise
		finally:
			log.debug('Calling cleanup on process monitor handler(s)')
			try:
				for l in self.handlers:
					if hasattr(l, 'cleanup'): l.cleanup()
			finally:
				self._cleanup()

	def running(self):
		"""Return the running status of the process monitor.
		
		@return: True if the process monitor background thread is still running. 
		@rtype: bool
		"""
		return self.thread.is_alive()

	
	def stop(self):
		"""Request the process monitor thread to terminate.
		
		Does not wait for the termination to complete. 
		
		"""
		self.thread.stop()

	# for implementation by subclasses

	def _getData(self, sample):
		"""Implement gathering of latest monitoring data. 
		
		Called on the background monitoring thread regularly.
		
		@param sample: An integer starting at 1 and incrementing each time 
		this method is called. 
		
		@return: A dictionary of (typically numeric) values, keyed by 
		L{ProcessMonitorKey}.
		@rtype: dict
		"""
		raise NotImplementedError('_getData is not implemented yet')

	def _cleanup(self):
		"""Perform implementation-specific cleanup. 
		
		Called on the background monitoring thread when the monitor is stopping. 
		
		"""
		pass

		
class WindowsProcessMonitor(BaseProcessMonitor):
	"""
	Windows implementation of the process monitor. 
	"""
	
	def start(self):
		# get the instance and instance number for this process id
		try:
			processInstanceName, processInstanceIndex = self.__win32GetInstance()
		except Exception as ex: # happens occasionally for no good reason
			log.debug('__win32GetInstance failed, will retry in case it was transient: %s', ex)
			time.sleep(1)
			processInstanceName, processInstanceIndex = self.__win32GetInstance()
		
		# create the process performance counters
		self._perfCounters={} # key=name, value=counter object
		process_query=win32pdh.OpenQuery()
		try:
			for counter in self._getPerfCounters():
				path = win32pdh.MakeCounterPath( (None, "Process", processInstanceName, None, processInstanceIndex, counter) )
				self._perfCounters[counter] = win32pdh.AddCounter(process_query, path)
		except Exception:
			win32pdh.CloseQuery(process_query)
		
		# this will be dealt with in cleanup
		self._perfQuery = process_query
		
		BaseProcessMonitor.start(self)

	def _cleanup(self):
		win32pdh.CloseQuery(self._perfQuery)

	def __win32GetInstance(self):
		# used during startup to convert a pid to the (processInstanceName, processInstanceIndex) tuple that the PDH API uses to identify processes
		
		log.debug('WindowsProcessMonitor: enumerating processes')
		
		# EnumObjectItems just returns whatever data was retrieved by EnumObjects so must call this first
		bRefresh = True
		if bRefresh: win32pdh.EnumObjects(None, None, 0, 1)
	
		# get the list of running processes
		log.debug('win32pdh.EnumObjectItems - getting process list')
		counters, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
		log.debug('win32pdh.EnumObjectItems - returned %d processes', len(instances))

		log.debug('WindowsProcessMonitor: finding process')
		
		# convert to a dictionary of process instance, to number of instances
		instanceDict = {}
		for i in instances:
			try: instanceDict[i] = instanceDict[i] + 1
			except KeyError: instanceDict[i] = 0
			
		# loop through to locate the instance and inum of the supplied pid
		instance = None
		inum = -1
		for instance, numInstances in list(instanceDict.items()):
			for inum in range(numInstances+1):
				try:
					value = self.__win32getProfileAttribute("Process", instance, inum, "ID Process")
					if value == self.pid:
						log.debug('__win32GetInstance: pid %s has instance=%s, inum=%s', self.pid, instance, inum)
						return instance, inum
				except Exception as ex:
					log.debug('__win32GetInstance: failed to get process id for %s: %s', instance, ex)
		
		log.debug('__win32GetInstance: pid %s has instance=%s, inum=%s', self.pid, instance, inum)
		raise Exception('Could not find running process %r'%(self.process or self.pid))

	def __win32getProfileAttribute(self, object, instance, inum, counter):
		# used during startup to get the pid
		
		# make the path, open and collect the query
		path = win32pdh.MakeCounterPath((None, object, instance, None, inum, counter))
		query = win32pdh.OpenQuery()
		try:
			hcounter = win32pdh.AddCounter(query, path)
			win32pdh.CollectQueryData(query)
			
			# format the counter value
			return win32pdh.GetFormattedCounterValue(hcounter, win32pdh.PDH_FMT_LARGE)[1]
		finally:
			win32pdh.CloseQuery(query)

	def _getPerfCounters(self):
		""" Get the list of string counter names to be monitored. These are passed to PdhMakeCounterPath. 
		"""
		return ["% Processor Time", "Working Set", "Virtual Bytes", "Private Bytes", "Thread Count", "Handle Count"]

	def __getPerfCounterValues(self):
		""" Get a dictionary containing the formatted counter values.
		"""
		retries = 10
		while True:
			retries -= 1
			try:
				win32pdh.CollectQueryData(self._perfQuery)
				break
			except Exception as ex:
				if retries == 0: 
					raise
				if self.process and not self.process.running(): raise
				log.debug('WindowsProcessMonitor: retrying getting perf counter values (%d remaining) after error: %s', retries, ex)
				time.sleep(1)
				
		data = {}
		for key, counter in self._perfCounters.items():
			try:
				data[key] = win32pdh.GetFormattedCounterValue(counter, win32pdh.PDH_FMT_LARGE)[1]
			except win32api.error:
				data[key] = None
		return data
		
	def _perfCountersToData(self, counterValues):
		data = {}
		data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = counterValues['% Processor Time']
		
		# the values are all 64-bit integers
		
		v = counterValues.get('Working Set',None)
		if v is not None: v = v//1024
		data[ProcessMonitorKey.MEMORY_RESIDENT_KB] = v

		v = counterValues.get('Virtual Bytes',None)
		if v is not None: v = v//1024
		data[ProcessMonitorKey.MEMORY_VIRTUAL_KB] = v
		
		v = counterValues.get('Private Bytes',None)
		if v is not None: v = v//1024
		data[ProcessMonitorKey.MEMORY_PRIVATE_KB] = v
		
		data[ProcessMonitorKey.THREADS] = counterValues['Thread Count']
		data[ProcessMonitorKey.KERNEL_HANDLES] = counterValues['Handle Count']
		data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = counterValues['% Processor Time']
		return data

	def _getData(self, sample):
		if sample == 1:
			# some keys such as processor time do not work until the 2nd time
			self.__getPerfCounterValues()
		return self._perfCountersToData(self.__getPerfCounterValues())

class SolarisProcessMonitor(BaseProcessMonitor): # pragma: no cover
	def _getData(self, sample):
		with process_lock:
			with os.popen("ps -p %s -o pcpu,rss,vsz" % (self.pid)) as fp:
				# skip header line
				info = fp.readlines()[1].strip()
				return {
					ProcessMonitorKeys.CPU_CORE_UTILIZATION: float(info[0]),
					ProcessMonitorKeys.MEMORY_RESIDENT_KB:   float(info[1]),
					ProcessMonitorKeys.MEMORY_VIRTUAL_KB:    float(info[2]),
				}

class LinuxProcessMonitor(BaseProcessMonitor):
	# also used for macos darwin
	
	INCLUDE_CHILD_PROCESSES = True
	"""
	Configuration option that specifies whether the LinuxProcessMonitor 
	will include the children of the specified process (that is, child 
	processes that exist at the point when the process monitor starts). 
	Note that other process monitors on other platforms currently do not 
	support this. 
	"""
	
	def start(self):
		# get the child process tree for this process
		if (self.INCLUDE_CHILD_PROCESSES):
			with process_lock:
				with os.popen("ps -o pid,ppid") as fp:
					psList = fp.readlines()
			self._pidTree = self.__findChildren(psList, self.pid)
		else:
			self._pidTree = [self.pid]

		BaseProcessMonitor.start(self)
	
	def __findChildren(self, psList, parentPid):
		children = []
		children.append(int(parentPid))
		
		for i in range(1, len(psList)):
			pid = int(psList[i].split()[0])
			ppid = int(psList[i].split()[1])
			if ppid == parentPid:
				children[len(children):] = self.__findChildren(psList, pid)
				
		return children

	def _getData(self, sample):
		with process_lock:
			with os.popen("ps -o pid,pcpu,rss,vsz") as fp: 
				info = fp.readlines()
			
			data = {
				ProcessMonitorKeys.CPU_CORE_UTILIZATION: 0,
				ProcessMonitorKeys.MEMORY_RESIDENT_KB: 0,
				ProcessMonitorKeys.MEMORY_VIRTUAL_KB: 0,
			}
			for i in range(1, len(info)):
				if int(info[i].split()[0]) in pidTree:
					thisdata = info[i].split()
					data[ProcessMonitorKeys.CPU_CORE_UTILIZATION] = data[ProcessMonitorKeys.CPU_CORE_UTILIZATION] + float(thisdata[1])
					
					# TODO: this looks like a bug - why are we setting it to an absolute value rather than accumulating for all child processes?
					data[ProcessMonitorKeys.MEMORY_RESIDENT_KB] = int(thisdata[2])
					data[ProcessMonitorKeys.MEMORY_VIRTUAL_KB] = int(thisdata[3])
			return data
			
if PLATFORM=='win32':
	ProcessMonitor = WindowsProcessMonitor
	"""Specifies the L{BaseProcessMonitor} subclass to be used for the current platform. """
elif PLATFORM=='sunos':
	ProcessMonitor = SolarisProcessMonitor
else:
	ProcessMonitor = LinuxProcessMonitor
