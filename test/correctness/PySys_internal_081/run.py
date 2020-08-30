import socket
import pysys
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
			self.waitForSocket(port, abortOnError=True, timeout=3)
		except pysys.exceptions.AbortExecution as e:
			self.log.info('Got exception as expected: %s: %s', type(e).__name__, e)
			del self.outcome[:]
		else:
			self.abort(FAILED, 'waitForSocket returned without error when it should have failed')
				
	def validate(self):
		self.assertTrue(True, assertMessage='verification is above')