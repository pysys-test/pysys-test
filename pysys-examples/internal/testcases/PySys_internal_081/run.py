import socket
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys import process_lock

class PySysTest(BaseTest):
	def execute(self):
		port = self.getNextAvailableTCPPort()
		
		with process_lock:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			s.bind(('', port))
			s.listen(5)
		# this should succeed as the socket is bound
		self.waitForSocket(port, abortOnError=True)
		# now shutdown the server socket
		with process_lock:
			s.close()
		
		# this should fail
		try:
			self.waitForSocket(port, abortOnError=True, timeout=2)
		except Exception as e:
			self.log.info('Got exception as expected: %s', e)
			del self.outcome[:]
		else:
			self.abort('waitForSocket returned without error when it should have failed')
				
	def validate(self):
		return
