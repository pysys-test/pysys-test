__pysys_title__   = r""" Demo of the manual test PySys UI used to check calculation of the Fibonacci series """
#                        ===============================================================================
__pysys_purpose__ = r""" This example testcase demonstrates the use of the manual tester user interface to script the execution of a manual testcase. The testcase describes to the user how to manually calculate the fibonacci series, and determine the correct value for the tenth entry
	"""

__pysys_created__ = "1999-12-31"

__pysys_groups__  = "manual"

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		if PLATFORM == 'darwin': self.skipTest('Manual tester does not currently work on this OS')
		self.startManualTester('input.xml')

	def validate(self):
		pass
