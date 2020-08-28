from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(FAILED, 'should not run')

	def validate(self):
		pass 
