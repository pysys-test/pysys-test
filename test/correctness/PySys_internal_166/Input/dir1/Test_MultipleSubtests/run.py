from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):

	# params can be specified here to define types
	maxHours = 0.0

	def execute(self):
		self.log.info('Mode=%s class=%s and params=%s', self.mode, self.mode.__class__.__name__, self.mode.params)
		self.log.info('Test field browser=%r'%self.browser)
		self.log.info('Test field maxHours=%r'%self.maxHours)
		
		self.addOutcome(PASSED, 'All ok')

	def validate(self):
		pass 
