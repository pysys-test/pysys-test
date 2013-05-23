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
# dealings in the software.

import collections, random, socket, sys, subprocess
from pysys import process_lock
from pysys.constants import *

# LRU queue of server TCP ports for allocation to tests which need to
# start TCP servers. Initialized to None since it might not actually be used.
# Properly initialize only on demand.
tcpServerPortPool = None

def getEphemeralTCPPortRange():
	"""Returns the range of TCP ports the operating system uses to allocate
	ephemeral ports from i.e. the ports allocated for the client side of a
	client-server connection. Returned as a tuple, 
	(ephemeral_low, ephemeral_high) or raises exception on error. 
	"""
	# Find the smallest and largest ephemeral port
	if PLATFORM == 'linux':
		f = open('/proc/sys/net/ipv4/ip_local_port_range')
		s = f.readline().split()
		ephemeral_low  = int(s[0])
		ephemeral_high = int(s[1])
		del f
	elif PLATFORM == 'sunos':
		def runNdd(driver, parameter):
			p = subprocess.Popen(['/usr/sbin/ndd', driver, parameter], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			return int(p.communicate()[0].strip())
		ephemeral_low = runNdd('/dev/tcp', 'tcp_smallest_anon_port')
		ephemeral_high = runNdd('/dev/tcp', 'tcp_largest_anon_port')
	elif PLATFORM == 'windows':
		ephemeral_low = 1025
		ephemeral_high = 5000 # The default
		import _winreg
		h = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters')
		try:
			ephemeral_high = _winreg.QueryValueEx(h, 'MaxUserPort')[0]
		except:
			# Accept the default if there isn't a value in the registry
			pass
		finally:
			_winreg.CloseKey(h)
			del h
	else:
		raise SystemError("No way of determining ephemeral port range on platform %s" % sys.platform)

	return (ephemeral_low, ephemeral_high)

def initializePortPool():
	"""Initialize the pool of ports we can allocate TCP server ports from
	i.e. ports to which processes can bind to without clashes with other
	processes
	"""

	global tcpServerPortPool

	ephemeral_low, ephemeral_high = getEphemeralTCPPortRange()

	# Allocate server ports from all non-privileged, non-ephemeral ports
	tcpServerPortPool = range(1024, ephemeral_low) + range(ephemeral_high,65536)

	# Randomize the port set to reduce the chance of clashes between
	# simultaneous runs on the same machine
	random.shuffle(tcpServerPortPool)

	# Convert to an LRU queue of ports
	tcpServerPortPool = collections.deque(tcpServerPortPool)

def portIsInUse(port):
	# Try to bind to it to see if anyone else is using it
	with process_lock:
		s = None
		try:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
			# Set SO_LINGER since we don't want any accidentally
			# connecting clients to cause the socket to hang
			# around
			if OSFAMILY == 'windows':
				s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 0)

			# Set non-blocking since we want to fail fast rather
			# than block
			s.setblocking(0)

			# Bind to empty host i.e wildcard interface
			try:
				s.bind(("", port))
			except Exception:
				# If we get any exception assume it is because
				# the port is in use
				s.close()
				return True

			# Listen may not be necessary, but on unix it seems to
			# help do a more complete shutdown if listen is called
			s.listen(1)
			try:
				s.shutdown(socket.SHUT_RDWR)
			except Exception:
				# Do nothing - on windows shutdown sometimes
				# fails even after listen
				pass
			s.close()
			return False
		except Exception, e:
			# Don't expect this but just in case
			print 'Here', e
			if s != None:
				s.close()
			return True

def allocateTCPPort():
	while True:
		port = tcpServerPortPool.popleft()
		if portIsInUse(port):
			# Toss the port back at the end of the queue
			tcpServerPortPool.append(port)
		else:
			return port


# Initialize the TCP port pool
initializePortPool()
