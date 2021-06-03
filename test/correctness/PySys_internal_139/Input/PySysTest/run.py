from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import warnings, traceback

class PySysTest(BaseTest):
	def execute(self):
		warnings.warn('This is simulated warning 1')
		warnings.warn('This is simulated warning 2')

	def validate(self):
		pass 
