from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.filecopy import filecopy 

class PySysTest(BaseTest):
	def execute(self):
		self.assertTrue(1==2)
		self.runAssert()

	def validate(self):
		self.runAssert()
		self.waitForGrep('run.log', expr='Assertion on', condition='==3', abortOnError=True, ignores=[' DEBUG '])
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:7\]')
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:20,run.py:8\]')
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:20,run.py:11\]')

	def runAssert(self):
		self.assertTrue(1==2)
