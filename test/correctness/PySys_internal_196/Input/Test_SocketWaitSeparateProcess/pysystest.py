__pysys_title__   = r""" Nested test that starts a TCP server and waits for it """ 
#                        ================================================================================

import os, sys, math, socket

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		port = self.getNextAvailableTCPPort()
		server = self.startPython([self.input+'/serversock.py', port], stdouterr='serversock', background=True)
		self.waitForSocket(port, process=server)

		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
			sock.connect(('localhost', port))
			sock.sendall(bytes("hello\n", "utf-8"))

			received = str(sock.recv(1024), "utf-8")
			self.log.info('Finished waiting for server data - should not happen since it blocks forever')
	
	def handleRunnerAbort(self, **kwargs): 
		self.log.info('Logging from customn handleRunnerAbort goes here')
		super().handleRunnerAbort(**kwargs)
		
	def validate(self):
		pass
