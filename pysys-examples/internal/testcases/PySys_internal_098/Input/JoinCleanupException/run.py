from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		def afunction(stopping, log, **kwargs):
			log.info('Hello from function thread')
			raise Exception('Simulated exception from background thread')
		
		f = self.startBackgroundThread('FunctionThread', afunction)
		# make sure thread has failed before cleanup begins
		for i in range(20):
			if f.exception is not None: break
			# don't use f.join() since to test this codepath we want to call f.join() only during cleanup
			f.thread.join(1)
		
		f.thread.join(5)
		
		self.log.info('End of execute()')

	def validate(self):
		pass 
