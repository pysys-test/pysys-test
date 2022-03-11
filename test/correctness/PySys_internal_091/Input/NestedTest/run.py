from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('About to print')
		print(u'Hello world! unicode plain')
		print(b'Hello world! bytes plain')
		print(u'Hello %s')
		print()
		print()
		print(u'After newlines')
		
		# check it's possible to specify non-ascii chars too
		print(u'Hello world! \xa3 unicode') # with pound sign
		self.log.info('Finished printing')
		
		self.addOutcome(PASSED)

	def validate(self):
		pass 
