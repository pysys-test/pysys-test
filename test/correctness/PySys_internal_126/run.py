import socket
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.allocport import portIsInUse
class PySysTest(BaseTest):
	def execute(self):
		for family, type, proto, can, addr in socket.getaddrinfo(socket.gethostname(), None)+socket.getaddrinfo('localhost', None):
			self.log.info("")
			self.log.info("--- Testing with %s address %s", family, addr)
			port = self.getNextAvailableTCPPort(hosts=[addr], socketAddressFamily=family)
			self.log.info("Successfully allocated port %d", port)
			self.waitForSocket(port=port, host='localhost', socketAddressFamily=family, abortOnError=False, timeout=0.1)
			self.assertThat('portIsInUse == False', portIsInUse=portIsInUse(port=port, host='localhost', socketAddressFamily=family))
			self.assertThat('portIsInUse == False', portIsInUse=portIsInUse(port=port, host='', socketAddressFamily=family))
			
			
	def validate(self):
		# check check we have no errors
		self.addOutcome(PASSED)