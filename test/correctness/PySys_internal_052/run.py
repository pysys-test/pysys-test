from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.assertLineCount('file1.txt', filedir=self.input, expr='oo', condition=' <=  0 ')
		self.assertLineCount('file1.txt', filedir=self.input, expr='oo.*', condition='==0')

		self.assertLineCount('file1.txt', filedir=self.input, expr='Foo', condition='==1')
		self.assertLineCount('file1.txt', filedir=self.input, expr='Fi', condition='>=15')
		self.waitForGrep('run.log', expr='Line count .*Fi.*>=15', timeout=30)
		
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		
	def validate(self):
		del self.outcome[:]

		self.assertLineCount('file1.txt', filedir=self.input, expr='This isnt present', condition='==0')

		self.assertGrep('run.log.proc', expr='Line count on file file1.txt ... passed')
		self.assertGrep('run.log.proc', expr=" Line count on file1.txt for \"Fi\" expected >=15 but got 1 ... failed")

		self.assertGrep('run.log.proc', expr='Line count on file1.txt for "oo" expected <=  0 but got 2; first is: "Foo is here"', literal=True)
		self.assertGrep('run.log.proc', expr='Line count on file1.txt for "oo.*" expected ==0 but got 2; first is: "oo is here"', literal=True)
