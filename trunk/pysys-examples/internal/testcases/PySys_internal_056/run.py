from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass
	def validate(self):
		self.assertTrue(True)
		self.assertTrue(False)
		self.addOutcome(TIMEDOUT, 'simulated timeout')
		self.assertTrue(True)
		self.assertGrep('not_there', expr="")
		self.checkOutcome()
		
	def checkOutcome(self):
		outcome = self.getOutcome()
		self.log.info('Outcome is %s' % self.outcome)
		self.log.info('Outcome is %s' % LOOKUP[outcome])
		
		self.outcome = [] 
		if outcome == BLOCKED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		