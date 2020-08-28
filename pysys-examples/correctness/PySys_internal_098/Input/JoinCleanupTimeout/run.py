from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		def afunction(stopping, log, **kwargs):
			log.info('Hello from function thread')
			stopping.wait(60*10) # this will block until cleanup
			stopping.clear()
			def functionThatAppearsToHang():
				log.info('Background thread got request to stop but wont do it just yet')
				stopping.wait(15) # this will cause it to timeout after cleanup
			functionThatAppearsToHang()
					
		f = self.startBackgroundThread('FunctionThread', afunction)
		assert f.joinTimeoutSecs > 0
		f.joinTimeoutSecs = 2 # don't waste a long time waiting
		
		self.log.info('End of execute()')

	def validate(self):
		pass 
