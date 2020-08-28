from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import random

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED, 'All good')
	def validate(self):
		pass 
