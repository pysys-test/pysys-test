from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertTrue(eval('1==1'))
		self.assertTrue(eval('12>=5'))
		self.assertTrue(True)
		self.assertTrue(eval('True'))
		self.assertTrue(eval('12*5>30'))
		
		self.assertTrue(eval('1!=1'))
		self.checkForFailedOutcome()
		
		self.assertTrue(eval('False'))
		self.checkForFailedOutcome()
		
		self.assertTrue(False)
		self.checkForFailedOutcome()
	
		
	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		