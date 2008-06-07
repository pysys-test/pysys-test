#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

import os, sys, string, time, thread, win32api, win32pdh

from pysys.constants import *


class ProcessMonitor:
	"""Win32 process monitor for the logging of process statistics.
	
	The win32 process monitor uses the win32pdh module to obtain and log to file statistics on a 
	given process as determined by the process id. Statistics obtained include the CPU usage (%), 
	the working set (virtual memory pages allocated), the virtual bytes (virtual address space 
	including shared memory segments), the private bytes (virtual address space not including 
	shared memory segments), and the number of process threads. All memory values are quoted in 
	KBytes. 
	
	Usage of the class is to create an instance specifying the process id, the logging interval and 
	the log file. Once created, the process monitor is started and stopped via its L{start()} and 
	L{stop()} methods. Process monitors are started as a separate thread, so control passes back to 
	the caller of the C{start()} method immediately. The format of the log file is tab separated, 
	with an initial timestamp used to denote the time the statistics were obtained, e.g. ::
	
		18/05/07 16:56:28       0       19464   46044   17708   1
		18/05/07 16:56:38       37      19536   46044   17716   1
		18/05/07 16:56:48       54      19616   46044   17984   1

	"""
	
	def __init__(self, pid, interval, file=None):
		"""Construct an instance of the process monitor.
		
		@param pid: The process id to monitor
		@param interval:  The interval in seconds to record the process statistics
		@param file: The full path to the file to log the process statistics
			
		"""
		self.pid = pid
		self.interval = interval
		if file:
			self.file = open(file, 'w', 0)
		else:	
			self.file = sys.stdout
			
			
	def __win32GetInstance(self, pid, bRefresh=0):
		# refresh allows process started after the python process
		# to be picked up
		if bRefresh: win32pdh.EnumObjects(None, None, 0, 1)
	
		# get a dictionary of all running processes, with the process
		# name as the key, and the number of instances as the value
		items, instances = win32pdh.EnumObjectItems(None, None, "Process", -1)
		instanceDict = {}
		for i in instances:
			try:
				instanceDict[i] = instanceDict[i] + 1
			except KeyError:
				instanceDict[i] = 0
			
		# find the instance name and the instance number for the requested
		# process ID. Once found, return the instance name and the instance
		# number so that this process can be tracked
		instance = None
		inum = -1
		for instance, numInstances in instanceDict.items():
			for inum in xrange(numInstances+1):
				try:
					value = self.__win32getProfileAttribute(instance, inum, "ID Process")
					if value == pid:
						return instance, inum
				except:
					pass

		return instance, inum


	def __win32getProfileAttribute(self, instance, inum, counter):
		# create the path for the counter of interest
		path = win32pdh.MakeCounterPath((None, "Process", instance, None, inum, counter))
		
		# open the query and add the counter to the query
		query = win32pdh.OpenQuery()
		hc = win32pdh.AddCounter(query, path)

		# collect the data for the query object. We need to collect the query data twice 
		# to be able to calculate the "% Processor Time" counter value 
		# (see http://support.microsoft.com/default.aspx?scid=kb;EN-US;q262938)
		win32pdh.CollectQueryData(query)
		if counter == "% Processor Time":
			time.sleep(0.25)	
			win32pdh.CollectQueryData(query)

		# Get the formatted value of the counter, remove and close the query
		# and return the counter value. Note that the process may have gone away
		# since getting the enum objects, so use try block and ignore exception
		value = None
		try:
			value =	 win32pdh.GetFormattedCounterValue(hc, win32pdh.PDH_FMT_LONG)[1]  
		except:
			pass

		win32pdh.RemoveCounter(hc)
		win32pdh.CloseQuery(query)
		return value


	def __win32LogProfile(self, instance, inum, interval, file):
		# open a query ready to perform repeat logging
		query = win32pdh.OpenQuery()
		
		# get a list of counter file handles, append them to a list
		# after adding them to the query
		fpcounters = []
		for i in "% Processor Time", "Working Set", "Virtual Bytes", "Private Bytes", "Thread Count":
			path = win32pdh.MakeCounterPath((None, "Process", instance, None, inum, i))
			try:
				fpcounters.append(win32pdh.AddCounter(query, path))
			except win32api.error: 
				fpcounters.append(0)
				pass
				
		# perform the repeated collection of the query data and formatted values for each of the 
		# counter file handles and log the data
		data = [0, 0, 0, 0, 0]
		while self.active:
			win32pdh.CollectQueryData(query)
			for i in range(len(fpcounters)):
				if fpcounters[i]:
					try:
						data[i] = win32pdh.GetFormattedCounterValue(fpcounters[i], win32pdh.PDH_FMT_LONG)[1]
					except win32api.error:
						data[i] = -1

			currentTime = time.strftime("%d/%m/%y %H:%M:%S", time.gmtime(time.time()))
			file.write( "%s\t%s\t%d\t%d\t%d\t%d\n" % (currentTime, data[0], float(data[1])/1024,
													  float(data[2])/1024, float(data[3])/1024, float(data[4])))
			time.sleep(interval)

		# on termination of the thread, remove the counters
		# and close the query cleanly
		for i in range(len(fpcounters)):
			if fpcounters[i]:  win32pdh.RemoveCounter(fpcounters[i])
		win32pdh.CloseQuery(query)


	def running(self):
		"""Return the running status of the process monitor.
		
		@return: The running status (L{pysys.constants.TRUE} | L{pysys.constants.FALSE})
		@rtype: integer
   		"""
		return self.active

	
	def start(self):
		"""Start the process monitor.
		
		"""
		self.active = 1
		instance, inum = self.__win32GetInstance(pid=self.pid, bRefresh=1)
		thread.start_new_thread(self.__win32LogProfile, (instance, inum, self.interval, self.file))
		

	def stop(self):
		"""Stop the process monitor.
		
		"""
		self.active = 0
		