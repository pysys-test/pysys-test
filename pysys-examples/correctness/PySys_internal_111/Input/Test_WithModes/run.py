from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Running test %s with mode "%s"', self.descriptor.id, self.mode)
		self.addOutcome(PASSED)

	def validate(self):
		pass 
