from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.filecopy import filecopy 

class PySysTest(BaseTest):
	def execute(self):
		self.assertThat('outcomeLocation == expected', outcomeLocation = self.getOutcomeLocation(), expected=(None,None), abortOnError=True)
		
		self.assertTrue(1==2)
		self.runAssert()


	def runAssert(self):
		self.assertTrue(1==2)

	def validate(self):
		self.runAssert()
		self.waitForGrep('run.log', expr='Assertion on', condition='==3', abortOnError=True, ignores=[' DEBUG ', 'Waiting for'])
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		loc = self.getOutcomeLocation()
		
		del self.outcome[:]
		self.log.info('---')
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:9\]')
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:14,run.py:10\]')
		self.assertGrep('run.log.proc', expr='Assertion.*failed \[run.py:14,run.py:17\]')
		
		self.assertThat('outcomeLocation[1] == expected', outcomeLocation=loc, expected='9')
		self.assertThat('outcomeLocation[0].endswith(os.sep+"run.py")', outcomeLocation=loc)
		self.assertThat('os.path.exists(outcomeLocation[0])', outcomeLocation=loc)
