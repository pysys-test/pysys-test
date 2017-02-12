import socket
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.log.info("Checking availability of port allocation ...")
		for i in range(0,4000):
			port = self.getNextAvailableTCPPort()
			try:
				sock = socket.socket()
				sock.bind(('127.0.0.1', port))
				sock.close()
			except:
				self.log.warn("Error binding to port %s", sys.exc_info()[1], exc_info=0)
				self.addOutcome(FAILED)
				break
				
	def validate(self):
		if not FAILED in self.outcome:
			self.addOutcome(PASSED)
