from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED)
		
		# this is a convenient place to test stringification of these objects
		self.log.info('NestedPass test object str=%s'%repr(str(self)))
		self.log.info('NestedPass test object repr=%s'%repr(self))
		self.log.info('NestedPass test cycle=%s'%self.testCycle)
		
		self.log.info('runner object str=%s'%repr(str(self.runner)))
		self.log.info('runner object repr=%s'%repr(self.runner))
		
	def validate(self):
		pass 
