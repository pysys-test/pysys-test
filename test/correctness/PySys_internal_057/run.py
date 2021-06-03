import socket
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.allocport import portIsInUse
class PySysTest(BaseTest):
	portsToAllocate = 4000
	def execute(self):
		self.log.info("Allocating %d IPv4 server ports and check we can use them", self.portsToAllocate)
		for i in range(0,self.portsToAllocate):
			port = self.getNextAvailableTCPPort()
			try:
				sock = socket.socket()
				try:
					sock.bind(('127.0.0.1', port))
				finally:
					sock.close()
			except Exception as e:
				self.log.warning("Error binding to port %s; in use=%s", sys.exc_info()[1], portIsInUse(port), exc_info=0)
				self.addOutcome(FAILED, "Error binding to 127.0.0.1 port %d (#%d): %s"%(port, i,e))
				break
				
	def validate(self):
		self.addOutcome(PASSED)