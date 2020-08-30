from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

Test2Symbol = 'foo'

class PySysTest(BaseTest):
	def execute(self):
		
		try:
			x = Test1Symbol
			self.log.info('Test2: Test1Symbol is defined')
		except Exception:
			self.log.info('Test2: Test1Symbol is not defined')
		

		try:
			y = Test2Symbol
			self.log.info('Test2: Test2Symbol is defined')
		except Exception:
			self.log.info('Test2: Test2Symbol is not defined')

		try:
			z = io.open
			self.log.info('Test2: io module is imported')
		except Exception:
			self.log.info('Test2: io module is not imported')

		try:
			xx = log
			self.log.info('Test2: log is imported')
		except Exception:
			self.log.info('Test2: log is not imported')

		self.addOutcome(PASSED)

	def validate(self):
		pass 
