from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		def afunction(stopping, log, **kwargs):
			log.info('Hello from function thread')
			raise Exception('Simulated exception from background thread')
		
		f = self.startBackgroundThread('FunctionThread', afunction)
		f.join(timeout=30, abortOnError=True) # should detect the exception
		
		self.log.info('End of execute()') # should not get here

	def validate(self):
		pass 
