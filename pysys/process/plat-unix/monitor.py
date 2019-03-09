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
import time, threading

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
			self.file = open(file, 'w')
		else:	
			self.file = sys.stdout		
	
		# normalise the CPU readings by the supplied factor
		self.numProcessors=1
		if "numProcessors" in kwargs: 
			self.numProcessors = int(kwargs["numProcessors"])
		
		
	def __findChildren(self, psList, parentPid):
		children = []
		children.append(int(parentPid))
		
		for i in range(1, len(psList)):
			pid = int(psList[i].split()[0])
			ppid = int(psList[i].split()[1])
			if ppid == parentPid:
				children[len(children):] = self.__findChildren(psList, pid)
				
		return children


	def __linuxLogProfile(self, pid, interval, file, includeChildren=True):
		# sleep - fixes weird problem of thread hanging?
		time.sleep(1)
		
		# get the child process tree for this process
		if (includeChildren):
			fp = os.popen("ps -o pid,ppid")
			psList = fp.readlines()
			fp.close()
			pidTree = self.__findChildren(psList, pid)
		else:
			pidTree = [pid]
		
		# perform the repeated collection of data for the profile. 
		try:
			while self.active:
				data = [0, 0, 0]
				fp = os.popen("ps -o pid,pcpu,rss,vsz")
				info = fp.readlines()
				fp.close()
				
				for i in range(1, len(info)):
					if int(info[i].split()[0]) in pidTree:
						data[0] = data[0] + float(info[i].split()[1])
						data[1] = int(info[i].split()[2])
						data[2] = int(info[i].split()[3])
	
				currentTime = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(time.time()))
				file.write( "%s\t%f\t%d\t%d\n" % (currentTime, float(data[0])/self.numProcessors, data[1], data[2]) )
				file.flush()
				time.sleep(interval)
	
			# clean up			
		finally:
			if file != sys.stdout: file.close()
			self.active = 0


	def __solarisLogProfile(self, pid, interval, file):	
		# perform the repeated collection of data for the profile. 
		data = [-1, -1, -1]
		try:
			while self.active:
				try:
					fp = os.popen("ps -p %s -o pcpu,rss,vsz" % (pid))
					info = fp.readlines()[1]
					for i in range(len(data)):
						data[i] = info[i].split()
					fp.close()
				except Exception:
					fp.close()
				currentTime = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(time.time()))
				file.write( "%s\t%s\t%s\t%s\n" % (currentTime, float(data[0])/self.numProcessors, data[1], data[2]) )
				file.flush()
				time.sleep(interval)
		finally:
			if file != sys.stdout: file.close()
			self.active = 0


	# public methods to start and stop a process monitor thread
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
		
		if PLATFORM == 'sunos':
			t = threading.Thread(target=self.__solarisLogProfile, args=(self.pid, self.interval, self.file))
		else:
			t = threading.Thread(target=self.__linuxLogProfile, args=(self.pid, self.interval, self.file))
		t.start()
		


	def stop(self):
		"""Stop the process monitor.
		
		"""
		self.active = 0
		



# used to run class from the command line
if __name__ == "__main__":
	if len(sys.argv) < 5:
		print("Usage: monprocess.py <pid> <interval> <duration> <filename>")
	else:
		try: 
			pid = int(sys.argv[1])
			interval = int(sys.argv[2])
			duration = int(sys.argv[3])
			file = sys.argv[4]
		except Exception: 
			print("Process ID, interval and duration should be valid integers")
			sys.exit(-1)	
		
		monitor = ProcessMonitor(pid, interval, file)
		monitor.start()
		time.sleep(duration)
		monitor.stop()

