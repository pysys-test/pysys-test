from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertTrue(True)
		self.assertTrue(False)
		self.assertTrue(True)
		self.checkOutcome()
		
	def checkOutcome(self):
		outcome = self.getOutcome()
		self.log.info('Outcome is %s' % self.outcome)
		self.log.info('Outcome is %s' % LOOKUP[outcome])
		
		self.outcome = [] 
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		