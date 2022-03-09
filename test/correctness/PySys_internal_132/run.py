from pysys.constants import *
from pysys.exceptions import *
from pysys.basetest import BaseTest
import signal

class PySysTest(BaseTest):
	
	def startTestProcess(self, **kwargs):
		try:
			return self.startPython([self.input+'/test.py']+kwargs.pop('arguments',[]), disableCoverage=True, displayName='python<%s>'%kwargs['stdouterr'], **kwargs)
		except Exception as ex: # test abort
			self.log.info('Suppressing exception: %s', ex)
	
	def execute(self):
		p = self.startTestProcess(stdouterr='timeout', arguments=['block'], background=True)

		self.signalProcess(p, signal.SIGTERM)

		self.waitForBackgroundProcesses(checkExitStatus=False, timeout=60)
	def validate(self):
		self.assertTrue(True, assertMessage='verification is above')