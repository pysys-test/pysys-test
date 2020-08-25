import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.log.info('Used myrunnerplugin to get Python version: %s', self.runner.myrunnerplugin.pythonVersion)
		self.assertThat('len(pythonVersionString) > 0', pythonVersionString=self.runner.myrunnerplugin.pythonVersion)

	