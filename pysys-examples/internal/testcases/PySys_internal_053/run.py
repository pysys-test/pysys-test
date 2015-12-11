from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLineCount('file1.txt', filedir=self.input, expr='Foo', condition='==1', assertMessage='Looking for Foo')
		self.assertLineCount('file1.txt', filedir=self.input, expr='Fi', condition='>=15', assertMessage='Looking for Fi')
		self.waitForSignal('run.log', expr='WARN  Looking for Fi ... failed', condition='>=1', timeout=5)
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='PASSED: Looking for Foo')
		self.assertGrep('run.log.proc', expr='FAILED: Looking for Fi .*is \'1\', does not match condition: \'>=15\'')
		
