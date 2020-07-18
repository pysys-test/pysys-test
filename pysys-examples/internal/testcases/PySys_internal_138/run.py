import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Log line 1')
		with self.pauseLogging():
			self.log.info('Log line 2')
		self.log.info('Log line 3')

		self.assertGrep('run.log', 'Log line 1')
		self.assertGrep('run.log', 'Log line 2', contains=False)
		self.assertGrep('run.log', 'Log line 3')
		
		pysys.internal.initlogging.pysysLogHandler.setLogHandlersForCurrentThread([])
		self.log.info('Log line 4')

	def validate(self):
		pass
	