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

"""
Dynamic TCP port allocation. 

This is used by the `pysys.process.user.ProcessUser` class (and its subclasses e.g. BaseTest) which should 
usually be used to access this functionality. 
"""

import collections, random, subprocess, sys
import io
import logging
import time
from pysys import process_lock
from pysys.constants import *

# LRU queue of server TCP ports for allocation to tests which need to
# start TCP servers. Initialized to None since it might not actually be used.
# Properly initialize only on demand.
tcpServerPortPool = None

_log = logging.getLogger('allocport')

def getEphemeralTCPPortRange():
	"""Returns the range of TCP ports the operating system uses to allocate
	ephemeral ports (the client side of the TCP connection). 
	
	This function is called by when `pysys.baserunner.BaseRunner` is constructed to configure the 
	pool of available server ports for `pysys.basetest.BaseTest.getNextAvailableTCPPort()`. 
	This ensures that no ports from the ephemeral (client-side) range are used for server ports 
	(which can cause random port clashes). 
	
	If required, the behaviour can be customized with environment variables:
	
	  - ``PYSYS_EPHEMERAL_TCP_PORT_RANGE=min-max`` This prevents `getEphemeralTCPPortRange` trying to detect the ephemeral 
	    port range and instead uses ``min`` as the bottom and ``max`` and the top end of the range.
	  - ``PYSYS_PORTS_FILE=file_path.txt`` This prevents `getEphemeralTCPPortRange` from even being called, and 
	    instead allows the available server ports to be enumerated in an ASCII text file, one per line. 
	
	:return: A tuple (ephemeral_min: int, ephemeral_max: int) giving the ephemeral port range for this platform. 
	:raises Exception: If the ephemeral port range cannot be determined, which will prevent PySys from running any tests. 
	"""
	if os.getenv('PYSYS_EPHEMERAL_TCP_PORT_RANGE'):
		envrange = os.environ['PYSYS_EPHEMERAL_TCP_PORT_RANGE'].split('-')
		if len(envrange)!=2: raise Exception('PYSYS_EPHEMERAL_TCP_PORT_RANGE environment variable must be of the form "low-high"')
		ephemeral_low, ephemeral_high = int(envrange[0].strip()), int(envrange[1].strip())
	# Find the smallest and largest ephemeral port
	elif PLATFORM == 'linux':
		with open('/proc/sys/net/ipv4/ip_local_port_range') as f:
			s = f.readline().split()
			ephemeral_low  = int(s[0])
			ephemeral_high = int(s[1])
	elif PLATFORM == 'sunos':
		def runNdd(driver, parameter):
			p = subprocess.Popen(['/usr/sbin/ndd', driver, parameter], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			return int(p.communicate()[0].strip())
		ephemeral_low = runNdd('/dev/tcp', 'tcp_smallest_anon_port')
		ephemeral_high = runNdd('/dev/tcp', 'tcp_largest_anon_port')
	elif PLATFORM == 'darwin':
		def runSysctl(parameter):
			p = subprocess.Popen(['/usr/sbin/sysctl', '-n', parameter], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			return int(p.communicate()[0].strip())
		ephemeral_low = runSysctl('net.inet.ip.portrange.first')
		ephemeral_high = runSysctl('net.inet.ip.portrange.last')
	elif PLATFORM == 'win32':
		ephemeral_low = 1025
		ephemeral_high = 5000 # The default
		if sys.version_info[0] == 2:
			import _winreg as winreg
		else:
			import winreg
		with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SYSTEM\CurrentControlSet\Services\Tcpip\Parameters') as h:
			try:
				ephemeral_high = winreg.QueryValueEx(h, 'MaxUserPort')[0]
			except Exception:
				# Accept the default if there isn't a value in the registry
				pass
	else:
		raise Exception("PySys cannot determine the ephemeral port range on platform %s (consider using the PYSYS_EPHEMERAL_TCP_PORT_RANGE=min-max or PYSYS_PORTS_FILE= environment variables)" % sys.platform)

	assert ephemeral_low <= ephemeral_high, [ephemeral_low, ephemeral_high]

	return (ephemeral_low, ephemeral_high)

def initializePortPool():
	"""Initialize the pool of ports we can allocate TCP server ports from
	i.e. ports that processes can bind to without clashes with other
	processes.
	
	Called from BaseRuner.__init__ (not when this module is imported) so that it's possible to monkey-patch 
	getEphemeralTCPPortRange() in user code (e.g. when the custom runner is imported) if required e.g. for a new platform. 
	
	:meta private: Not public API
	"""

	global tcpServerPortPool
	assert tcpServerPortPool is None, 'Cannot call initializePortPool() more than once per process'

	portsfile = os.getenv('PYSYS_PORTS_FILE',None)
	if portsfile:
		with io.open(portsfile, 'r', encoding='utf-8') as f:
			tcpServerPortPool = []
			for l in f:
				l = l.strip()
				if l: tcpServerPortPool.append(int(l))
		if not tcpServerPortPool:
			raise Exception('No ports found in %s'%portsfile)
	else: 
		ephemeral_low, ephemeral_high = getEphemeralTCPPortRange()

		# Allocate server ports from all non-privileged, non-ephemeral ports
		tcpServerPortPool = list(range(1024, ephemeral_low)) + list(range(ephemeral_high,65536))

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
		except Exception as e:
			# Don't expect this but just in case
			_log.error('Exception from port allocator: %s - %s', e.__class__.__name__, e)
			if s != None:
				s.close()
			return True

def allocateTCPPort():
	t = time.time()
	while time.time()-t < TIMEOUTS['WaitForAvailableTCPPort']:
		
		# in case we've allocated all the available ports, loop 
		# until another test terminates and free up some ports
		try:
			port = tcpServerPortPool.popleft()
		except Exception:
			time.sleep(2)
			continue
		
		if portIsInUse(port):
			# Toss the port back at the end of the queue
			tcpServerPortPool.append(port)
			time.sleep(0.5) # avoid spinning
		else:
			return port
	raise Exception('Could not allocate TCP server port; other tests are currently using all the available ports')

class TCPPortOwner(object):
	"""
	Class that allocates a free server port when constructed, 
	and returns it to the pool of available ports when `cleanup` is called. 
	
	:ivar int ~.port: The port allocated and owned by this instance. 
	"""
	def __init__(self):
		self.port = allocateTCPPort()

	def cleanup(self):
		"""Must be called when this port is no longer needed to return it to PySys' pool of available ports. 
		"""
		tcpServerPortPool.append(self.port)
