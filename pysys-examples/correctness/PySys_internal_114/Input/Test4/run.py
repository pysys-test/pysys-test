from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('%s execution order hint = "%s"', self.descriptor.id, self.descriptor.executionOrderHint)
		self.addOutcome(PASSED)

	def validate(self):
		pass 
