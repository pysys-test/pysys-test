from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Running with mode: %s', self.mode)
		self.addOutcome(PASSED)

	def validate(self):
		pass 
