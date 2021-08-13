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
Contains the process monitoring API used by L{pysys.basetest.BaseTest.startProcessMonitor}.

The main components are the L{pysys.process.monitor.BaseProcessMonitor} class, L{ProcessMonitorKey} constants for identifying 
columns and the default L{ProcessMonitorTextFileHandler} class for writing monitoring information to a file. 
"""

__all__ = ['BaseProcessMonitor', 'BaseProcessMonitorHandler', 'ProcessMonitorTextFileHandler', 'ProcessMonitorKey']

import os, sys, string, time, threading, logging, multiprocessing
from pysys import process_lock
from pysys.constants import *
from pysys.utils.pycompat import *


if PLATFORM=='win32' and 'sphinx' not in sys.modules:
	import win32api, win32pdh, win32con, win32process # pragma: no cover

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
	
	The type is C{int}. 
	"""

	CPU_TOTAL_UTILIZATION = 'CPU total %'
	"""Total utilization % of all available CPU cores, with a maximum value of 100%.
	
	If you have 2 cores and one of them is 50% utilized, the value would be 25%.
	
	The type is C{int}. 
	"""
	
	MEMORY_RESIDENT_KB = 'Resident memory kB'
	"""
	Resident / working set memory usage. 
	
	This is the non-swapped physical memory, and is usually a good statistic to 
	use for checking for memory leaks and excessive memory usage. 

	On Unix it is equivalent to `rss`/`RES` and on Windows to the working set 
	memory usage.
	
	The type is C{int}. 
	"""
	
	MEMORY_VIRTUAL_KB = 'Virtual memory kB'
	"""
	Virtual memory of the process including memory that is swapped out. 
	
	On Unix it is equivalent to `vsz`/`VIRT`, and on Windows to the 
	current page file usage. 
	
	The type is C{int}. 
	"""
	
	DATE_TIME = 'Time'
	"""String representation of the date and local time for this sample 
	in yyyy-mm-dd HH:MM:SS format. 
	"""

	DATE_TIME_LEGACY = 'Time (legacy)'
	"""String representation of the date and local time for this sample in 
	a format compatible with v1.3.0 and earlier versions of PySys. 
	
	This is %d/%m/%y %H:%M:%S on Windows and %m/%d/%y %H:%M:%S on Unix. 
	
	@deprecated: Use L{DATE_TIME} if possible. 
	"""
	
	SAMPLE = 'Sample'
	"""A counter starting from 1 and incrementing with each new set of 
	sample data.
	
	The type is C{int}. 
	"""
	

class BaseProcessMonitorHandler(object):
	"""
	Interface to be implemented to provide a custom handler that records 
	or processes data from a L{BaseProcessMonitor}. 
	"""
	def handleData(self, data, **kwargs):
		"""
		Called on a background thread each time a new sample of monitoring 
		data is available. 
		
		:param data: a dictionary whose keys are from L{ProcessMonitorKey} 
			(or any new keys added by custom process monitor implementations). 
			The dictionary values are of type C{int}, C{float} or C{string}. 
		
		:param kwargs: Reserved for future use. 
		"""
		raise NotImplementedError('Not implemented yet')
	
	def cleanup(self):
		"""
		Called on a background thread to perform cleanup for this handler, 
		for example closing file handles. 
		"""
		pass

class ProcessMonitorTextFileHandler(BaseProcessMonitorHandler):
	"""Handles process monitor data by writing the data as delimited values to 
	a file, usually with tab separated values (.tsv). 
	
	A new line is written every time the process monitor polls for a new sample 
	of data. By default a header line starting with `#` is included at the 
	start of the file to indicate the column headings. 
	
	If any value cannot be retrieved or is unavailable on this operating 
	system, a -1 value will be written instead. 
	
	Uses default values set on the instance unless keyword overrides 
	are provided; see L{setDefaults}.

	:param str file: An absolute path string or open file handle to which 
		process monitor data lines will be written. 
	
	:param list[str] columns: An ordered list of the columns from L{ProcessMonitorKey} that 
		should be included in the file. If not specified, the columns specified 
		by L{DEFAULT_COLUMNS} will be used. 
	
	:param str delimiter: The delimiter string used between each column. 
		If not specified, the string specified by L{DEFAULT_DELIMITER} will be 
		used. 
	
	:param bool writeHeaderLine: Determines whether a header line prefixed 
		by `#` will be written at the start of the file. If not overridden, the 
		default is taken from L{DEFAULT_WRITE_HEADER_LINE}.

	"""
	
	DEFAULT_COLUMNS = [
		ProcessMonitorKey.DATE_TIME, 
		ProcessMonitorKey.CPU_CORE_UTILIZATION, 
		ProcessMonitorKey.MEMORY_RESIDENT_KB,
		ProcessMonitorKey.MEMORY_VIRTUAL_KB,
		]
	"""The default columns to write to the file.
	
	If using a process monitor that comes with PySys, the values are from 
	L{ProcessMonitorKey}.
	
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

	DEFAULT_DELIMITER = u'\t'
	"""
	The delimiter used between each column. Usually a tab character. 

	See L{setDefaults}.
	"""
	
	@staticmethod
	def setDefaults(columns, delimiter=None, writeHeaderLine=None):
		"""Static helper method for setting the default columns or 
		C{writeHeaderLine} setting for all tests that use the 
		C{ProcessMonitorTextFileHandler}. 
		
		This method could be called from a custom runner's 
		L{pysys.baserunner.BaseRunner.setup} method in order to take effect 
		for all tests. 
		
		Do not call this from within an individual testcase since that 
		could cause unwanted interference between different testcases. 
		
		:param columns: A list of the colums to be included, using values from
			L{ProcessMonitorKey}. Since additional columns may be added to the end 
			of L{DEFAULT_COLUMNS} in future releases, when calling this method you 
			should specify all the columns you want explicitly including the 
			current defaults rather than writing `DEFAULT_COLUMNS+[...]`. 
		
		:param delimiter: The delimiter string used between each column. 
				
		:param writeHeaderLine: Specifies whether a header line beginning 
			with `#` should be written at the start of the file. 
		"""
		if columns: ProcessMonitorTextFileHandler.DEFAULT_COLUMNS = list(columns)
		if writeHeaderLine is not None: ProcessMonitorTextFileHandler.DEFAULT_WRITE_HEADER_LINE = writeHeaderLine
		if delimiter is not None: ProcessMonitorTextFileHandler.DEFAULT_DELIMITER = delimiter
	
	def __init__(self, file, columns=None, delimiter=None, writeHeaderLine=None):
		self.columns = columns or self.DEFAULT_COLUMNS
		self.delimiter = delimiter or self.DEFAULT_DELIMITER
		if PY2 and isinstance(self.delimiter, str): self.delimiter=self.delimiter.decode('utf-8')
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
			self.stream.write(u'#%s\n'%self.delimiter.join(self.columns).replace(u' ',u'_'))
		self.stream.flush()
	
	def handleData(self, data):
		values = [data.get(k,None) for k in self.columns]
		line = self.delimiter.join([
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
	
	For detail on the statistic keys available from the standard 
	process monitor classes see L{ProcessMonitorKey}.
	
	The most convenient way to start the default process monitor for this 
	operating system is to use L{pysys.basetest.BaseTest.startProcessMonitor}.
	
	You can create a custom subclass if you need to add support for a new OS 
	or return additional monitoring statistics. For example, you could 
	create a custom process monitor for Java processes that returned 
	heap size and thread count, or you could create a simple process monitor 
	wrapper around a Python library that provides a wider set of monitoring 
	statistics, such as psutil. The fields and methods starting with a 
	single underscore `_` can be used or overridden by custom subclasses. 
	To start the process monitor from a custom class, simply ensure you have 
	passed the owner basetest to its constructor and then call the L{start} 
	method. 

	Monitors are automatically terminated during cleanup at the end 
	of a test, or can be manually stopped before that using the L{stop} method. 

	:param owner: The BaseTest owning this monitor. 
	
	:param process: The process wrapper object. A numeric pid can be specified 
		instead but with reduced functionality, so use a process object if you 
		have one. 
	
	:param interval: The interval in seconds between polling for each data 
		sample. 
	
	:param pmargs: Keyword arguments to allow parameterization of the 
		returned data. An exception will be raised for any arguments not 
		expected by this class. 
	"""
	
	def __init__(self, owner, process, interval, handlers, **pmargs):
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
		
		assert handlers, 'Must have at least one handler for the data generated by the process monitor'
		self.handlers = handlers
		"""The list of handlers that will be notified each time the process 
		is polled for new data. """
		
		self.thread = None
		""" The background thread that responsible for monitoring the process. """
		
		self._stopping = None
		"""The C{threading.Event} that is set when the background thread 
		should begin stopping. Call C{wait} on this object instead of sleeping 
		to get fast wake-ups during cleanup. 
		"""
		
		try:
			self._cpuCount = multiprocessing.cpu_count()
			"""The count of available CPU cores on this host, used 
			for scaling up the CPU_TOTAL_UTILIZATION. 
			"""
		except Exception as ex: # pragma: no cover
			log.debug('Failed to get multiprocessing.cpu_count: %s', ex)
			self._cpuCount = 1
		
	def start(self):
		"""
		Called on the main test thread to start monitoring in the background. 
		
		Performs any required initialization of data structures then 
		starts the background thread. 
		
		:return: This instance. 
		:rtype: L{BaseProcessMonitor}
		"""
		# executed on main thread - the best place to perform initial setup so we 
		# get an immediate error if it fails
		self.thread = self.owner.startBackgroundThread(str(self), self.__backgroundThread)
		return self
	
	def __str__(self): return 'ProcessMonitor<%s>'%('%s pid=%d'%(self.process,self.pid) if self.process else self.pid)
	
	def _preprocessData(self, data):
		""" Called in the background thread with the data dictionary from 
		each poll of the process, to allow OS-agnostic pre-processing and 
		addition of derived data keys such as the date and time. 
		
		:param data: The dictionary of process monitoring data. This method 
			may add or modify the contents of this dictionary. 
		
		"""
		
		datetime = time.localtime(time.time())
		data[ProcessMonitorKey.DATE_TIME] = time.strftime("%Y-%m-%d %H:%M:%S", datetime)
		data[ProcessMonitorKey.DATE_TIME_LEGACY] = time.strftime(
			"%d/%m/%y %H:%M:%S" if IS_WINDOWS else "%m/%d/%y %H:%M:%S", datetime)
		
		if data.get(ProcessMonitorKey.CPU_CORE_UTILIZATION,None) is not None:

			data[ProcessMonitorKey.CPU_TOTAL_UTILIZATION] = int(data[ProcessMonitorKey.CPU_CORE_UTILIZATION] / self._cpuCount)
			
			if self.__numProcessors > 1:
				# undocumented, for compatibility only
				data[ProcessMonitorKey.CPU_CORE_UTILIZATION] = data[ProcessMonitorKey.CPU_CORE_UTILIZATION] / self.__numProcessors
	
	def __backgroundThread(self, log, stopping):
		self._stopping = stopping # for use by other process monitor methods
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
		
		:return: True if the process monitor background thread is still running. 
		:rtype: bool
		"""
		return self.thread.is_alive()

	
	def stop(self, timeout=None):
		"""Request the process monitor thread to terminate.
		
		Waits for the termination to complete if possible, but does not throw an exception if it fails. 
		
		:param float timeout: Overrides the maximum time we will wait for the monitor to stop. By default this is 
			``['WaitForProcessStop']`` from `constants.TIMEOUTS`. 
		
		"""
		self.thread.stop()
		self.thread.join(timeout=timeout, abortOnError=False)

	# for implementation by subclasses

	def _getData(self, sample):
		"""Implement gathering of latest monitoring data. 
		
		Called on the background monitoring thread regularly.
		
		:param sample: An integer starting at 1 and incrementing each time 
			this method is called. 
		
		:return: A dictionary of (typically numeric) values, keyed by 
			L{ProcessMonitorKey}.
		:rtype: dict
		"""
		raise NotImplementedError('_getData must be implemented by subclass')

	def _cleanup(self):
		"""Perform implementation-specific cleanup. 
		
		Called on the background monitoring thread when the monitor is stopping. 
		
		"""
		pass
