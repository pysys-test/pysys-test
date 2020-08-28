import pysys
from pysys.constants import *


class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		def getValue():
			# In a more realistic example, this might be the output from a process
			raise Exception("Didn't work this time")
	
		v = None
		for retry in range(5):
			try:
				v = getValue()
				if v: break
			except Exception as ex:
				self.log.info('Failed to get the value we want to test (retry #%d): %s', retry, ex)
		
		if v:
			self.assertThat('v > 100', v = v)
			
		# If we don't execute any assertions then the default outcome of NOTVERIFIED is used
	
	def validate(self):	
		pass
	