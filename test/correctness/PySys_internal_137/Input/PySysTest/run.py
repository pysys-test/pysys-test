from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import logging
import pysys

class PySysTest(BaseTest):
	def execute(self):
		# can access method and fields of our test plugin using self.alias.XXX
		myPythonVersion = self.myorg.getPythonVersion()
		self.assertThat('len(actual) > 0', actual__eval='myPythonVersion')

		# One of the things runners can do is add to runDetails
		self.assertThat('len(actual) > 0', actual__eval='self.runner.runDetails["myPythonVersion"]')

	def validate(self):
		pass 
