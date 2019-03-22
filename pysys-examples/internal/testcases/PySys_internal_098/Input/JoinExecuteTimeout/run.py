from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		def afunction(stopping, log, **kwargs):
			log.info('Hello from function thread')			
			while not stopping.is_set():
				stopping.wait(1.0)
		
		f = self.startBackgroundThread('FunctionThread', afunction)
		f.join(1) # will fail cos we didn't ask it to stop. but it should now be asked to terminate
		
		f.join(timeout=30, abortOnError=True) # should succeed since the above will have implicitly cancelled it
		self.assertTrue(not f.isAlive(), assertMessage='MethodThread is no longer alive')
		
		self.log.info('End of execute()')

	def validate(self):
		pass 
