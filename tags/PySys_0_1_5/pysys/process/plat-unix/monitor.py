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

import os, sys, string, time, thread

from pysys.constants import *


class ProcessMonitor:
	def __init__(self, pid, interval, file=None):
		self.pid = pid
		self.interval = interval
		if file:
			self.file = open(file, 'w', 0)
		else:	
			self.file = sys.stdout		
	
		
	def findChildren(self, psList, parentPid):
		children = []
		children.append(int(parentPid))
		
		for i in range(1, len(psList)):
			pid = int(string.split(psList[i])[0])
			ppid = int(string.split(psList[i])[1])
			if ppid == parentPid:
				children[len(children):] = self.findChildren(psList, pid)
				
		return children


	def linuxLogProfile(self, pid, interval, file, includeChildren=TRUE):
		# sleep - fixes weird problem of thread hanging?
		time.sleep(1)
		
		# get the child process tree for this process
		if (includeChildren):
			fp = os.popen("ps -o pid,ppid")
			psList = fp.readlines()
			fp.close()
			pidTree = self.findChildren(psList, pid)
		else:
			pidTree = [pid]
		
		# perform the repeated collection of data for the profile. 
		while self.active:
			data = [0, 0, 0]
			fp = os.popen("ps -o pid,pcpu,rss,vsz")
			info = fp.readlines()
			fp.close()
			
			for i in range(1, len(info)):
				if int(string.split(info[i])[0]) in pidTree:
					data[0] = data[0] + float(string.split(info[i])[1])
					data[1] = int(string.split(info[i])[2])
					data[2] = int(string.split(info[i])[3])

			currentTime = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(time.time()))
			file.write( "%s\t%f\t%d\t%d\n" % (currentTime, data[0], data[1], data[2]) )
			time.sleep(interval)


	def solarisLogProfile(self, pid, interval, file):	
		# perform the repeated collection of data for the profile. 
		data = [-1, -1, -1]
		while self.active:
			try:
				fp = os.popen("ps -p %s -o pcpu,rss,vsz" % (pid))
				info = fp.readlines()[1]
				for i in range(len(data)):
					data[i] = string.split(info)[i]
				fp.close()
			except:
				fp.close()
			currentTime = time.strftime("%m/%d/%y %H:%M:%S", time.gmtime(time.time()))
			file.write( "%s\t%s\t%s\t%s\n" % (currentTime, data[0], data[1], data[2]) )
			time.sleep(interval)


	# public methods to start and stop a process monitor thread
	def start(self):
		self.active = 1
		if PLATFORM == 'sunos':
			thread.start_new_thread(self.solarisLogProfile, (self.pid, self.interval, self.file))
		elif PLATFORM == 'linux':
			thread.start_new_thread(self.linuxLogProfile, (self.pid, self.interval, self.file))


	def stop(self):
		self.active = 0
		



# used to run class from the command line
if __name__ == "__main__":
	if len(sys.argv) < 5:
		print "Usage: monprocess.py <pid> <interval> <duration> <filename>"
	else:
		try: 
			pid = int(sys.argv[1])
			interval = int(sys.argv[2])
			duration = int(sys.argv[3])
			file = sys.argv[4]
		except: 
			print "Process ID, interval and duration should be valid integers"
			sys.exit(-1)	
		
		monitor = ProcessMonitor(pid, interval, file)
		monitor.start()
		time.sleep(duration)
		monitor.stop()

