from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.abort(FAILED, 'simulated abort')
	def validate(self):
		pass 
