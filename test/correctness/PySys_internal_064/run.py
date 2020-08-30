from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		
		with open(self.output+'/success.txt', 'w') as f:
			f.write('foobar\ngoodexpr\nfoobar')
		with open(self.output+'/bad.txt', 'w') as f:
			f.write('foobar\ntimestamp ERROR should be ignored\n2016-01-02 12:53:55 ERROR something terrible happened    \n')
			
		self.waitForGrep('success.txt', expr='goodexpr', errorExpr=['badexpr'])
		try:
			self.waitForGrep('bad.txt', expr='goodexpr', errorExpr=['not found', ' ERROR '], abortOnError=True, ignores=['should be ignore.'])
			self.addOutcome(FAILED, 'Expected abort')
		except AbortExecution as e:
			del self.outcome[:]
			self.assertThat('%s == %s', e.outcome, BLOCKED)
			self.log.info('Got abort: %s', e.value)
			self.assertEval('{outcomeReason}.startswith("\\"ERROR something terrible happened\\"")', outcomeReason=e.value)
			self.assertEval("'aiting for ' in {outcomeReason}", outcomeReason=e.value)
			self.assertEval("'bad.txt' in {outcomeReason}", outcomeReason=e.value)

	def validate(self):
		pass # see above
