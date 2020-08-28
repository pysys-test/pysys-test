from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import logging
import pysys

class PySysTest(BaseTest):
	def execute(self):
		self.skipTest('No-op test') # just so there are multiple results and hence we get to see the runDetails printed

	def validate(self):
		pass 
