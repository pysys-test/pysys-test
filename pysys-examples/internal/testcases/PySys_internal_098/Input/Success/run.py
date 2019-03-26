from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		def afunction(stopping, log):
			log.info('Hello from function thread')
		
		f = self.startBackgroundThread('FunctionThread', afunction)
		
		m = self.startBackgroundThread('MethodThread', target=self.instancemethod, kwargsForTarget={'param': 123})
		self.assertTrue(m.is_alive(), assertMessage='MethodThread is initially alive')

		m.stop()

		m.join(timeout=30, abortOnError=True) # should succeed since the above will have implicitly cancelled it
		self.assertTrue(not m.isAlive(), assertMessage='MethodThread is no longer alive')
		self.assertTrue(m.exception is None, assertMessage='MethodThread .exception was not set since it occurred during thread stopping')
		
		self.log.info('End of execute()')

	def validate(self):
		pass 

	def instancemethod(self, param, log, stopping):
		log.info('Hello from instance method thread: param=%d', param)
		while not stopping.is_set():
			stopping.wait(10*60)
		# these exceptions don't cause test failures
		raise Exception('Simulated error after instance method thread was asked to stop')
		