from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import random
class PySysTest(BaseTest):
	def execute(self):
		# wait a random amount of time up to a second
		self.wait(random.random()*1.0)
		self.addOutcome(PASSED)
	def validate(self):
		pass 
