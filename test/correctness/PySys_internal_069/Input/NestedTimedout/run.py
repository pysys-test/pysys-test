from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(TIMEDOUT, 'Reason for timed out outcome is general tardiness')
	def validate(self):
		pass 
