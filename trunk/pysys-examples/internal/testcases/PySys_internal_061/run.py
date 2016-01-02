from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertTrue(1==2)
		self.assertTrue(1==1)
		self.assertFalse(1==1)
		self.addOutcome(DUMPED_CORE)

	def validate(self):
		pass
