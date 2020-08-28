from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED)
		self.startPython([self.input+'/hello.py'], stdouterr='hello') # just to generate some code coverage
		self.reportPerformanceResult(123, 'A performance key', '/s')
		
		self.runner.publishArtifact(self.output+'/run.log', category='MyCustomCategory')
		
	def validate(self):
		pass 
