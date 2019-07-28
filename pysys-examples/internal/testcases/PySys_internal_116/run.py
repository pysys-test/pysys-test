from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		with open(self.output+'/results.txt', 'w') as f:
			self.assertEval('len({myString}) == {expectedLength}', myString='a "\n\\ b', expectedLength=7, somethingrandom=True)
			f.write('expected success: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			del self.outcome[:]
			#self.addOutcome(NOTVERIFIED, override=True)

			self.assertEval('len({myString}) == {expectedLength}', expectedLength=1000, myString='a "\n\\ b')
			f.write('expected failure: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			#self.addOutcome(NOTVERIFIED, override=True)
			del self.outcome[:]
		
			self.assertEval('invalid SYNTAX {param1}:', param1=123)
			f.write('expected failure: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			#self.addOutcome(NOTVERIFIED, override=True)
			del self.outcome[:]
	
			self.assertEval('len({myPath}) > 4', myPath=self.output+'/foo')
			f.write('expected success: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			#self.addOutcome(NOTVERIFIED, override=True)
			del self.outcome[:]
			
	def validate(self):
		self.assertDiff('results.txt', 'ref-results.txt')
