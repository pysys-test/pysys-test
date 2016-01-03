from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLineCount('file1.txt', filedir=self.input, expr='Foo', condition='==1')
		self.assertLineCount('file1.txt', filedir=self.input, expr='Fi', condition='>=15')
		self.waitForSignal('run.log', expr='Line count on file1.txt for "Fi">=15 ... failed', timeout=5)
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Line count on input file file1.txt ... passed')
		self.assertGrep('run.log.proc', expr="Line count on file1.txt for \"Fi\">=15 ... failed")
