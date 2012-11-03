from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertTrue(True)
		self.assertTrue(False)
		self.waitForFile('not_there', timeout=1)
		self.assertTrue(True)
		self.checkOutcome()
		
	def checkOutcome(self):
		outcome = self.getOutcome()
		self.outcome = [] 
		if outcome == TIMEDOUT: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		