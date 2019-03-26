from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		
		with open(self.output+'/success.txt', 'w') as f:
			f.write('foobar\ngoodexpr\nfoobar')
		with open(self.output+'/bad.txt', 'w') as f:
			f.write('foobar\ntimestamp ERROR should be ignored\n2016-01-02 12:53:55 ERROR something terrible happened    \n')
			
		self.waitForSignal('success.txt', expr='goodexpr', errorExpr=['badexpr'])
		try:
			self.waitForSignal('bad.txt', expr='goodexpr', errorExpr=['not found', ' ERROR '], abortOnError=True, ignores=['should be ignore.'])
			self.addOutcome(FAILED, 'Expected abort')
		except AbortExecution as e:
			del self.outcome[:]
			self.assertThat('%s == %s', e.outcome, BLOCKED)
			self.log.info('Got abort: %s', e.value)
			self.assertThat('\'%s\'.startswith("\\"ERROR something terrible happened\\"")', e.value)
			self.assertThat("'ait for signal ' in '%s'", e.value)
			self.assertThat("'bad.txt' in '%s'", e.value)

	def validate(self):
		pass # see above
