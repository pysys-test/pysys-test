from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLineCount('file1.txt', filedir=self.input, expr='Foo', condition='==1', assertMessage='Looking for Foo')
		self.assertLineCount('file1.txt', filedir=self.input, expr='Fi', condition='>=15', assertMessage='Looking for Fi')
		self.waitForGrep('run.log', expr='Looking for Fi.*failed', timeout=5, ignores=[' DEBUG '])
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Looking for Foo: Line count on .* ... passed')
		self.assertGrep('run.log.proc', expr='Looking for Fi: Line count .* >=15.* ... failed')
		
