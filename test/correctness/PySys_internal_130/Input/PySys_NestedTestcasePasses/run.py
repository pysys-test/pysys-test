from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import random

class PySysTest(BaseTest):
	param1 = 'default value'
	param2 = 'default value'
	def execute(self):
		self.log.info('param1="%s"', self.param1)
		self.log.info('param2="%s"', self.param2)
		self.addOutcome(PASSED, 'All good')
	def validate(self):
		pass 
