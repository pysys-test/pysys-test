from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Bar', assertMessage='looking for Bar')
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE, assertMessage='looking for Foo')
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE, assertMessage='looking for Foo again')
		
		self.waitForSignal('run.log', expr='looking for Foo again', condition='>=1', timeout=5)
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
	
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='PASSED for looking for Bar')
		self.assertGrep('run.log.proc', expr='PASSED for looking for Foo')
		self.assertGrep('run.log.proc', expr='PASSED for looking for Foo again')
			
