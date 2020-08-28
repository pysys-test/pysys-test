from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import warnings, traceback

class PySysTest(BaseTest):
	
	def badCleanup(self):
		raise Exception('My cleanup function error')
	def execute(self):
		self.addCleanupFunction(self.badCleanup, ignoreErrors=True)

	def validate(self):
		pass 
