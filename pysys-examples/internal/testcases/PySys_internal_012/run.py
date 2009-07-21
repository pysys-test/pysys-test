from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertLineCount(file='file1.txt', filedir=self.input, expr='cat', condition='==4')
