#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
import platform
from pysys import process_lock
from pysys.constants import *
from pysys.utils.fileutils import openfile

# LRU queue of server TCP ports for allocation to tests which need to
# start TCP servers. Initialized to None since it might not actually be used.
# Properly initialize only on demand.
tcpServerPortPool = None

_log = logging.getLogger('pysys.allocport')

def getEphemeralTCPPortRange():
	"""Returns the minimum and maximum TCP ports this operating system uses to allocate
	ephemeral ports (the client side of the TCP connection). 
	
	This function is used by `getServerTCPPorts()` to ensure that no ephemeral/client-side ports are allocated for 
	server-side purposes by PySys (this could cause random port clashes). 
	
	If the available server ports are overridden using the ``PYSYS_PORTS`` or ``PYSYS_PORTS_FILE`` environment 
	variables, this function is not called. 
	
	:return: A tuple (ephemeral_min: int, ephemeral_max: int) giving the ephemeral port range for this platform. 
	:raises Exception: If the ephemeral port range cannot be determined, which will prevent PySys from running any tests. 
	"""
	# Find the smallest and largest ephemeral port
	if PLATFORM == 'linux':
		port_file = '/proc/sys/net/ipv4/ip_local_port_range'
		if not os.path.exists(port_file):
			# There's no perfect default that works for all OSes (and the config may be customized by the OS anyway), 
			# but it's useful to avoid an error to help on environments like Windows Subsystem for Linux v1. 
			# We pick the IANA range as our default
			ephemeral_low, ephemeral_high = 49152, 65535
			_log.warning('PySys cannot determine the local/ephemeral port range on this OS (%s) as "%s" is missing; falling back to default IANA range %d-%d. Consider using the PYSYS_PORTS=minport-maxport environment variable to explicitly configure the range of non-ephemeral/server ports for PySys to use.', platform.platform(), port_file, ephemeral_low, ephemeral_high)
		else:
			with openfile(port_file) as f:
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

def getServerTCPPorts():
	"""Returns a list of the TCP ports that PySys tests can use when starting servers that listen on a port. 
	
	This function is usually called when `pysys.baserunner.BaseRunner` is constructed to help decide the 
	pool of available ports that can be allocated by `pysys.basetest.BaseTest.getNextAvailableTCPPort()`. 

	PySys treats all ports from 1024-65536 as server ports except for the client-side ephemeral port range 
	as determined by `getEphemeralTCPPortRange()`. Alternatively, the set of server ports can be overridden by the 
	following environment variables:
	
	  - ``PYSYS_PORTS=minport-maxport,port,...`` PySys will use the specified ports and/or port ranges (inclusive) 
	    allocating server ports.  
	  - ``PYSYS_PORTS_FILE=file_path.txt`` PySys will use ports from the specified ASCII text file, one port per line. 

	If using these variables, be sure to avoid none of the ports reserved for ephemeral use is in the set of server 
	ports you specify. 

	:return: A list or set of all the server ports that can be used, e.g. [1024, 1025, ...]. 
	:raises Exception: If the port range cannot be determined, which will prevent PySys from running any tests. 
	"""
	if os.getenv('PYSYS_PORTS', None):
		specs = os.environ['PYSYS_PORTS'].split(',')
	elif os.getenv('PYSYS_PORTS_FILE',None):
		with io.open(os.environ['PYSYS_PORTS_FILE'], 'r', encoding='utf-8') as f:
			specs = f.readlines()
	else: 
		ephemeral_low, ephemeral_high = getEphemeralTCPPortRange()
		# The standard implementation: allocate server ports from all non-privileged, non-ephemeral ports
		return list(range(1024, ephemeral_low)) + list(range(ephemeral_high,65536))

	ports = set()
	for x in specs:
		x = x.strip()
		if len(x)==0: continue
		
		if '-' in x:
			envrange = x.split('-')
			for p in range(int(envrange[0].strip()), int(envrange[1].strip())+1):
				ports.add(p)
		else:
			ports.add(int(x.strip()))
	return ports


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

	tcpServerPortPool = list(getServerTCPPorts())

	# Randomize the port set to reduce the chance of clashes between
	# simultaneous runs on the same machine
	random.shuffle(tcpServerPortPool)

	# Convert to an LRU queue of ports
	tcpServerPortPool = collections.deque(tcpServerPortPool)

def portIsInUse(port, host='', socketAddressFamily=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
	# Try to bind to the post on the specified address to see if anyone else is using it
	with process_lock:
		s = socket.socket(socketAddressFamily, type, proto=proto)
		try:
		
			# Set SO_LINGER since we don't want any accidentally
			# connecting clients to cause the socket to hang
			# around
			if IS_WINDOWS:
				s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 0)

			# Set non-blocking since we want to fail fast rather
			# than block
			s.setblocking(0)

			try:
				s.bind( (host, port) )
			except Exception as e:
				# If we get any exception assume it is because
				# the port is in use
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
			
		except Exception as e:
			# Don't expect this but just in case
			_log.error('Exception from port allocator portIsInUse check for %s:%d - %s: %s', host or 'INADDR_ANY', port, e.__class__.__name__, e)
			return True
		finally:
			s.close()
	return False

def allocateTCPPort(hosts=['', 'localhost'], socketAddressFamily=socket.AF_INET, type=socket.SOCK_STREAM, proto=0):
	# nb: expose socket type and protocol number here but not higher up the stack just in case someone needs them, but 
	# not very likely
	t = time.time()
	while time.time()-t < TIMEOUTS['WaitForAvailableTCPPort']:
		
		# in case we've allocated all the available ports, loop 
		# until another test terminates and free up some ports
		try:
			port = tcpServerPortPool.popleft()
		except Exception:
			time.sleep(2)
			continue
		
		if any(portIsInUse(port, socketAddressFamily=socketAddressFamily, type=type, proto=proto, host=host) for host in hosts):
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
	
	:param list(Str) hosts: A list of the host names or IP addresses to check when establishing that a potential 
		allocated port isn't already in use by a process outside the PySys framework. 
		By default we check ``""`` (which corresponds to ``INADDR_ANY`` and depending on the OS means 
		either one or all non-localhost IPv4 addresses) and also ``localhost``. 
		Many machines have multiple network cards each with its own host IP address, and typically you'll only be using 
		one of them in your test, most commonly ``localhost``. If you do know which host/IP you'll actually be using, 
		just specify that directly to save time, and avoid needlessly opening remote ports on hosts you're not using. 
		A list of available host addresses and corresponding family/type/proto can be found from 
		``socket.getaddrinfo('', None)``.
	
	:param int socketAddressFamily: The address family to use when checking if the port is in use, e.g. to indicate 
		IPv4 vs IPv6. See ``socket.socket`` in the Python standard library for more information. 

	:ivar int ~.port: The port allocated and owned by this instance. 
	"""
	def __init__(self, hosts=['', 'localhost'], socketAddressFamily=socket.AF_INET):
		self.port = allocateTCPPort(hosts=hosts, socketAddressFamily=socketAddressFamily)

	def cleanup(self):
		"""Must be called when this port is no longer needed to return it to PySys' pool of available ports. 
		"""
		tcpServerPortPool.append(self.port)
