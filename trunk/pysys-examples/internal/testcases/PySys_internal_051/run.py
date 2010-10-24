from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLineCount('file1.txt', filedir=self.input, expr='Foo', condition='==1')
		self.assertLineCount('file1.txt', filedir=self.input, expr='Fi', condition='>=15')
		self.waitForSignal('run.log', expr='Line count', condition='>=2')
		
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log', expr='Line count on input file file1.txt ... passed')
		self.assertGrep('run.log', expr='Line count on input file file1.txt ... failed \[1>=15\]')
		