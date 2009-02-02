from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.startManualTester('input.xml')

	def validate(self):
		pass
