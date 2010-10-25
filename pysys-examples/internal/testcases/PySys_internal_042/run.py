from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertFalse(eval('1==2'))
		self.assertFalse(eval('12<=5'))
		self.assertFalse(False)
		self.assertFalse(eval('False'))
		self.assertFalse(eval('12*5<30'))
		
		self.assertFalse(eval('1==1'))
		self.checkForFailedOutcome()
		
		self.assertFalse(eval('True'))
		self.checkForFailedOutcome()
		
		self.assertFalse(True)
		self.checkForFailedOutcome()
	
		
	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		