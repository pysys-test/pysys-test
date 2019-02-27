from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.foo = 2

	def validate(self):
		self.assertTrue(self.foo==2)
