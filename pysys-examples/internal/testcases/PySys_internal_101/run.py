import io
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):

		outcomes = []
		
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )
		
		self.addOutcome(NOTVERIFIED, 'My not verified reason')
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )

		self.addOutcome(BLOCKED, 'My blocked reason')
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )

		self.addOutcome(PASSED, 'My passed reason', override=True)
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )

		self.addOutcome(SKIPPED, 'My skipped reason')
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )

		self.addOutcome(FAILED, 'My failed reason 1', override=True)
		self.addOutcome(FAILED, 'My failed reason 2')
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )

		self.addOutcome(PASSED, 'My passed reason', override=True)
		outcomes.append( (self.getOutcome(), self.getOutcomeReason() ) )
		
		with io.open(self.output+'/outcomes.txt', 'w', encoding='ascii') as f:
			for o, r in outcomes:
				f.write(u'%s: "%s"\n'%(LOOKUP[o], r))
	def validate(self):
		self.addOutcome(PASSED, 'reset', override=True)
		self.logFileContents('outcomes.txt')
		self.assertDiff('outcomes.txt', 'ref_outcomes.txt')
		