from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Sample message info')
		self.log.warning('Sample %s warn', 'message')
		try:
			raise Exception('My exception')
		except Exception:
			self.log.exception('Sample message at error with exception trace: ')

		self.addOutcome(SKIPPED, 'skipped reason message', abortOnError=False)
		self.addOutcome(BLOCKED, 'blocked reason message', abortOnError=False)
		self.addOutcome(DUMPEDCORE, 'dumpedcore reason message', abortOnError=False)
		self.addOutcome(TIMEDOUT, 'timedout reason message', abortOnError=False)
		self.addOutcome(FAILED, 'failed reason message', abortOnError=False)
		self.addOutcome(NOTVERIFIED, 'notverified reason message', abortOnError=False)
		self.addOutcome(PASSED, 'passed reason message', abortOnError=False)
		self.abort(FAILED, 'abort reason message')
	def validate(self):
		pass 
