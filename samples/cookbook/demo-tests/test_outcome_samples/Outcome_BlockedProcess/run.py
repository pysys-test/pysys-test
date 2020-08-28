import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		server = self.startPython([self.input+'/my_server.py'], stdouterr='my_server', background=True)
		
		# The errorExpr/process arguments ensure we abort with a really informative message if the server fails to start, 
		# instead of waiting ages and then timing out
		self.waitForGrep('my_server.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], 
			process=server, timeout=TIMEOUTS['WaitForProcess']*2) 
		
	def validate(self):	
		self.assertGrep('my_server.out', r' (ERROR|FATAL|WARN) .*', contains=False)
