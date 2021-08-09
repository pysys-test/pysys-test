from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):

	def execute(self):
		self.log.info('Mode=%s (repr=%r) class=%s and params=%s', self.mode, self.mode, self.mode.__class__.__name__, self.mode.params)
		self.log.info('Test field browser=%r'%self.mode.params['browser'])
		self.log.info('Test field maxHours=%r'%self.mode.params['maxHours'])
		self.log.info('Test field iterations=%r'%self.mode.params['iterations'])
	
		self.addOutcome(PASSED, 'All ok')

	def validate(self):
		pass 
