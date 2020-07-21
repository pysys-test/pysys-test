import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import logging

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Log line 1')
		with self.disableLogging():
			self.log.info('Log line 2')
		self.log.info('Log line 3')

		self.assertGrep('run.log', 'Log line 1')
		self.assertGrep('run.log', 'Log line 2', contains=logging.getLogger('pysys.disabledLogging').isEnabledFor(logging.DEBUG))
		self.assertGrep('run.log', 'Log line 3')
		
		pysys.internal.initlogging.pysysLogHandler.setLogHandlersForCurrentThread([])
		self.log.info('Log line 4')

	def validate(self):
		pass
	