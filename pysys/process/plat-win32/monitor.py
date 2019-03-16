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
import os, sys, string, time, threading, logging

if 'epydoc' not in sys.modules:
	import win32api, win32pdh

from pysys import log
from pysys.constants import *


class ProcessMonitor(object):
	"""Process monitor for the logging of process statistics.
	
	The process monitor uses either the win32pdh module (windows systems) or the ps command line utility 
	(unix systems) to obtain and log to file statistics on a given process as determined by the process id. 
	Usage of the class is to create an instance specifying the process id, the logging interval and the log 
	file. Once created, the process monitor is started and stopped via its L{start} and L{stop} methods. 
	Process monitors are started as a separate thread, so control passes back to the caller of the start method 
	immediately.
	
	On windows systems, statistics obtained include the CPU usage (%), the working set (memory pages allocated), 
	the virtual bytes (virtual address space including shared memory segments), the private bytes (virtual 
	address space not including shared memory segments), the number of process threads and the number of 
	handles. All memory values are quoted in KBytes and the CPU precentage represents the usage over all available 
	processors. A CPU usage of 100% represents a single CPU fully utilized; it is therefore possible to obtain CPU 
	usage figures of over 100% on multi-core processors. The format of the log file is tab separated, with 
	timestamps used to denote the time each measurement was obtained, e.g. ::		
	
		Time                    CPU   Working  Virtual  Private  Threads Handles
		------------------------------------------------------------------------
		09/16/08 14:20:44       80    125164   212948   118740   44      327
		09/16/08 14:20:49       86    125676   213972   120128   44      328
		09/16/08 14:20:54       84    125520   212948   119116   44      328
		09/16/08 14:20:59       78    125244   212948   119132   44      328


	On unix systems, statistics obtained include the CPU usage (%), the resident memory (via the rss format specifier
	to ps), and the virtual memory (via the vsz format spepcifier to ps). All memory values are quoted in KBytes and 
	the CPU precentage represents the usage over all available processors. A CPU usage of 100% represents a single 
	CPU fully utilized; it is therefore possible to obtain CPU usage figures of over 100% on multi-core processors. 
	The format of the log file is tab separated, with timestamps used to denote the time each measurement was obtained, 
	e.g. ::		

		Time                    CPU        Resident  Virtual
		----------------------------------------------------
		09/16/08 14:24:10       69.5       89056     1421672
		09/16/08 14:24:20       73.1       101688    1436804
		09/16/08 14:24:30       82.9       102196    1436516
		09/16/08 14:24:40       89.1       102428    1436372
		09/16/08 14:24:50       94.2       104404    1438420


	Both windows and unix operating systems support the numProcessors argument in the variable argument list in order 
	to normalise the CPU statistics gathered by the number of available CPUs.

	"""
	
	def __init__(self, pid, interval, file=None, process=None, **kwargs):
		"""Construct an instance of the process monitor.
		
		@param pid: The process id to monitor
		@param interval:  The interval in seconds to record the process statistics
		@param file: The full path to the file to log the process statistics
		@param kwargs: Keyword arguments to allow platform specific configurations	
		
		"""
		self.pid = pid
		self.interval = interval
		if file:
			self.file = open(file, 'w')
		else:	
			self.file = sys.stdout
		
		# normalise the CPU readings by the supplied factor
		self.numProcessors=1
		if "numProcessors" in kwargs: 
			self.numProcessors = int(kwargs["numProcessors"])
		self.process = process
				
							
	def __win32GetInstance(self, pid, bRefresh=0):
		# convert a pid to the (processname, instancecounter) that the PDH API uses to identify processes
		
		if bRefresh: win32pdh.EnumObjects(None, None, 0, 1)
	
		# get the list of processes running
		log.debug('win32pdh.EnumObjectItems - getting process list')
		counters, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
		log.debug('win32pdh.EnumObjectItems - returned %d processes', len(instances))
		
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
					if value == pid:
						log.debug('__win32GetInstance: pid %s has instance=%s, inum=%s', pid, instance, inum)
						return instance, inum
				except Exception as ex:
					log.debug('__win32GetInstance: failed to get process id for %s: %s', instance, ex)
		
		log.debug('__win32GetInstance: pid %s has instance=%s, inum=%s', pid, instance, inum)
		raise Exception('Could not find running process %d'%pid)

	def __win32getProfileAttribute(self, object, instance, inum, counter):
		# make the path, open and collect the query
		path = win32pdh.MakeCounterPath((None, object, instance, None, inum, counter))
		query = win32pdh.OpenQuery()
		hcounter = win32pdh.AddCounter(query, path)
		win32pdh.CollectQueryData(query)
		
		# format the counter value
		value = None
		try:
			value =	 win32pdh.GetFormattedCounterValue(hcounter, win32pdh.PDH_FMT_LONG)[1]  
		except Exception:
			pass
		
		# tidy up and return the value
		win32pdh.RemoveCounter(hcounter)
		win32pdh.CloseQuery(query)
		return value


	def __win32LogProfile(self, instance, inum, interval, file):
		try:
			# create the process performance counters
			process_counters=[]
			process_query=win32pdh.OpenQuery()
			for counter in "% Processor Time", "Working Set", "Virtual Bytes", "Private Bytes", "Thread Count", "Handle Count":
				path = win32pdh.MakeCounterPath( (None, "Process", instance, None, inum, counter) )
				process_counters.append(win32pdh.AddCounter(process_query, path))
			
			def collectData():
				retries = 10
				while True:
					retries -= 1
					try:
						win32pdh.CollectQueryData(process_query)
						return
					except Exception:
						if retries == 0: 
							raise
						if not self.process.running(): return
						time.sleep(1)
					
			collectData()
			
			# perform the continual data collection until the thread is no longer active
			data = [0]*(len(process_counters))	
			try:
				while self.active:
					collectData()
		
					for i in range(len(process_counters)):
						try:
							data[i] = win32pdh.GetFormattedCounterValue(process_counters[i], win32pdh.PDH_FMT_LARGE)[1]
						except win32api.error:
							data[i] = -1
				
					currentTime = time.strftime("%d/%m/%y %H:%M:%S", time.gmtime(time.time()))
					file.write( "%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (currentTime, data[0]//self.numProcessors, float(data[1])/1024,
															  float(data[2])/1024, float(data[3])/1024, float(data[4]), float(data[5])))
					file.flush()
					time.sleep(interval)
			finally:
				# clean up
				for c in process_counters:
					win32pdh.RemoveCounter(c)
				win32pdh.CloseQuery(process_query)
				if file != sys.stdout: file.close()
				self.active = 0
		except Exception:
			if self.process and not self.process.running():
				return
			raise

	def running(self):
		"""Return the running status of the process monitor.
		
		@return: The running status (True | False)
		@rtype: integer
		"""
		return self.active

	
	def start(self):
		"""Start the process monitor.
		
		"""
		self.active = 1
		
		# get the instance and instance number for this process id
		try:
			instance, inum = self.__win32GetInstance(pid=self.pid, bRefresh=1)
		except Exception: # happens occasionally for no good reason
			time.sleep(1)
			instance, inum = self.__win32GetInstance(pid=self.pid, bRefresh=1)
		
		
		# log the stats in a separate thread
		t = threading.Thread(target=self.__win32LogProfile, args=(instance, inum, self.interval, self.file))
		t.start()

	def stop(self):
		"""Stop the process monitor.
		
		"""
		self.active = 0
		
			
if __name__ == "__main__":
	items, instances = win32pdh.EnumObjectItems(None, None, "System", -1)
	print("System - available counters are; ")
	for item in items: print(item)
	print() 

	items, instances = win32pdh.EnumObjectItems(None, None, "Processor", -1)
	print("Processor - available counters are; ")
	for item in items: print(item)
	print() 

	items, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
	print("Process - available counters are; ")
	for item in items: print(item)
	print() 

	items, instances = win32pdh.EnumObjectItems(None, None, "Thread", -1)
	print("Thread - available counters are; ")
	for item in items: print(item)
	print()

	 