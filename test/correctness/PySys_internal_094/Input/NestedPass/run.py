from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED)
		
		# this is a convenient place to test stringification of these objects
		self.log.info('NestedPass test object str=%s'%repr(str(self)))
		
	def validate(self):
		pass 
