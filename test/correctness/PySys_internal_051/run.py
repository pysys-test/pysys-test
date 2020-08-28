from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Bar', assertMessage='Looking for Bar')
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE, assertMessage='Looking for Foo')
		self.assertLastGrep('file1.txt', filedir=self.input, expr='Foo', contains=FALSE, assertMessage='Looking for Foo again')
		
		self.waitForGrep('run.log', expr='Looking for Foo again', condition='>=1', timeout=5, ignores=[' DEBUG '])
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
	
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Looking for Bar ... passed')
		self.assertGrep('run.log.proc', expr='Looking for Foo ... passed')
		self.assertGrep('run.log.proc', expr='Looking for Foo again ... passed')
			
