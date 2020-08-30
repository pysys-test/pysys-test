from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.write_text('myfile.txt', 'goodexpr')
		
		self.waitForGrep('myfile.txt', expr='goodexpr', errorIf=lambda: True)
		try:
			self.waitForGrep('myfile.txt', expr='missing_expr', errorIf=lambda: self.getExprFromFile('myfile.txt', 'good.*', returnNoneIfMissing=True))
			self.addOutcome(FAILED, 'Expected abort')
		except AbortExecution as e:
			del self.outcome[:]
			self.assertThat('%s == %s', e.outcome, BLOCKED)
			self.log.info('Got abort: %s', e.value)
			self.assertThat('outcomeReason.endswith(expected)', 
				outcomeReason=e.value, expected=' aborted due to errorIf=goodexpr')

	def validate(self):
		pass # see above
