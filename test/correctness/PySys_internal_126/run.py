import socket
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.allocport import portIsInUse
class PySysTest(BaseTest):
	def execute(self):
		def subtest(addrinfo):
			family, type, proto, can, addr = addrinfo
			key = f'{repr(family)} {addr}'
			self.log.info(f"{key} started")
			port = self.getNextAvailableTCPPort(hosts=[addr], socketAddressFamily=family)
			self.log.info(f"{key} successfully allocated port %d", port)
			self.waitForSocket(port=port, host='localhost', socketAddressFamily=family, abortOnError=False, timeout=0.1)
			self.assertThat('portIsInUse == False', portIsInUse=portIsInUse(port=port, host='localhost', socketAddressFamily=family), family=family, addr=addr)
			self.assertThat('portIsInUse == False', portIsInUse=portIsInUse(port=port, host='', socketAddressFamily=family), family=family, addr=addr)


		list(self.createThreadPoolExecutor().map(subtest, socket.getaddrinfo(socket.gethostname(), None)+socket.getaddrinfo('localhost', None)))
			
	def validate(self):
		# check check we have no errors
		self.addOutcome(PASSED)