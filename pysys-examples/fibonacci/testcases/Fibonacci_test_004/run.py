import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		if PLATFORM == 'darwin': self.skipTest('Manual tester does not currently work on this OS')
		self.startManualTester('input.xml')

	def validate(self):
		pass
