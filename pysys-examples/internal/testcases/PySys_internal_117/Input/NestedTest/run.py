from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		TIMEOUTS['WaitForAvailableTCPPort'] = 3
		with open(self.output+'/got-ports.txt', 'w') as f:
			for i in range(10):
				try:
					p = self.getNextAvailableTCPPort()
				except Exception as ex:
					self.log.info('Port allocation failed: %s - %s', ex.__class__.__name__, ex)
					return
				else:
					self.log.info('Successfully allocated port %d'%p)
					f.write(str(p))
					f.write('\n')

	def validate(self):
		pass 
