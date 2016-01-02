#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net

import os, sys, string, time, thread, logging, win32api, win32pdh

from pysys import log
from pysys.constants import *


class ProcessMonitor:
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
	
	def __init__(self, pid, interval, file=None, **kwargs):
		"""Construct an instance of the process monitor.
		
		@param pid: The process id to monitor
		@param interval:  The interval in seconds to record the process statistics
		@param file: The full path to the file to log the process statistics
		@param kwargs: Keyword arguments to allow platform specific configurations	
		
		"""
		self.pid = pid
		self.interval = interval
		if file:
			self.file = open(file, 'w', 0)
		else:	
			self.file = sys.stdout
		
		# normalise the CPU readings by the supplied factor
		self.numProcessors=1
		if kwargs.has_key("numProcessors"): 
			self.numProcessors = int(kwargs["numProcessors"])
				
							
	def __win32GetInstance(self, pid, bRefresh=0):
		if bRefresh: win32pdh.EnumObjects(None, None, 0, 1)
	
		# get the list of processes running
		items, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
		
		# convert to a dictionary of process instance, to number of instances
		instanceDict = {}
		for i in instances:
			try: instanceDict[i] = instanceDict[i] + 1
			except KeyError: instanceDict[i] = 0
			
		# loop through to locate the instance and inum of the supplied pid
		instance = None
		inum = -1
		for instance, numInstances in instanceDict.items():
			for inum in xrange(numInstances+1):
				try:
					value = self.__win32getProfileAttribute("Process", instance, inum, "ID Process")
					if value == pid:
						return instance, inum
				except:
					pass

		return instance, inum


	def __win32GetThreads(self, pid, bRefresh=0):
		if bRefresh: win32pdh.EnumObjects(None, None, 0, 1)

		# get the list of threads running
		items, instances = win32pdh.EnumObjectItems(None, None, "Thread", -1)
				
		# convert to a dictionary of thread instance, to number of instances
		instanceNum = []
		instanceDict = {}
		for i in instances:
			try: instanceDict[i] = instanceDict[i] + 1
			except KeyError: instanceDict[i] = 0
			instanceNum.append(instanceDict[i])
			
		# loop through to locate the instance and inum of each thread for the supplied process id
		threads=[]
		for i in range(0, len(instances)):
			try:	
				value = self.__win32getProfileAttribute("Thread", instances[i], instanceNum[i], "ID Process")
				if value == pid: threads.append((instances[i], instanceNum[i]))
			except:
				pass
		return threads


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
		except:
			pass
		
		# tidy up and return the value
		win32pdh.RemoveCounter(hcounter)
		win32pdh.CloseQuery(query)
		return value


	def __win32LogProfile(self, instance, inum, threads, interval, file):
		
		# create the process performance counters
		process_counters=[]
		process_query=win32pdh.OpenQuery()
		for counter in "Working Set", "Virtual Bytes", "Private Bytes", "Thread Count", "Handle Count":
			path = win32pdh.MakeCounterPath( (None, "Process", instance, None, inum, counter) )
			process_counters.append(win32pdh.AddCounter(process_query, path))
		win32pdh.CollectQueryData(process_query)
					
		# create the thread performance counter
		thread_counters=[]
		thread_query=win32pdh.OpenQuery()
		for (instance, inum) in threads:
			path=win32pdh.MakeCounterPath( (None, "Thread", instance, None, inum, "% Processor Time") )
			thread_counters.append(win32pdh.AddCounter(thread_query, path))
		win32pdh.CollectQueryData(thread_query)
	
		# perform the continual data collection until the thread is no longer active
		data = [0]*(len(process_counters)+1)	
		while self.active:
			win32pdh.CollectQueryData(process_query)
			win32pdh.CollectQueryData(thread_query)

			for i in range(len(process_counters)):
				try:
					data[i+1] = win32pdh.GetFormattedCounterValue(process_counters[i], win32pdh.PDH_FMT_LONG)[1]
				except win32api.error:
					data[i+1] = -1
		
			data[0]=0
			for i in range(0, len(thread_counters)):
				try:
					data[0]=data[0]+win32pdh.GetFormattedCounterValue(thread_counters[i], win32pdh.PDH_FMT_LONG)[1] 
				except:
					pass
	
			currentTime = time.strftime("%d/%m/%y %H:%M:%S", time.gmtime(time.time()))
			file.write( "%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (currentTime, data[0]/self.numProcessors, float(data[1])/1024,
													  float(data[2])/1024, float(data[3])/1024, float(data[4]), float(data[5])))
			time.sleep(interval)

		# clean up
		for c in process_counters:
			win32pdh.RemoveCounter(c)
		win32pdh.CloseQuery(process_query)
		for c in thread_counters:
			win32pdh.RemoveCounter(c)
		win32pdh.CloseQuery(thread_query)
		if file != sys.stdout: file.close()

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
		instance, inum = self.__win32GetInstance(pid=self.pid, bRefresh=1)

		# get the instance and instance number for each thread of this process id
		threads = self.__win32GetThreads(pid=self.pid, bRefresh=1)
		
		# log the stats in a separate thread
		thread.start_new_thread(self.__win32LogProfile, (instance, inum, threads, self.interval, self.file))
		

	def stop(self):
		"""Stop the process monitor.
		
		"""
		self.active = 0
		
			
if __name__ == "__main__":
	items, instances = win32pdh.EnumObjectItems(None, None, "System", -1)
	print "System - available counters are; "
	for item in items: print item
	print 

	items, instances = win32pdh.EnumObjectItems(None, None, "Processor", -1)
	print "Processor - available counters are; "
	for item in items: print item
	print 

	items, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
	print "Process - available counters are; "
	for item in items: print item
	print 

	items, instances = win32pdh.EnumObjectItems(None, None, "Thread", -1)
	print "Thread - available counters are; "
	for item in items: print item
	print

	 