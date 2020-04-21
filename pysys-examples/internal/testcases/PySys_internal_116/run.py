from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		with open(self.output+'/results.txt', 'w') as f:
			self.assertEval('len({myString}) == {expectedLength}', myString='a "\n\\ b', expectedLength=7, somethingrandom=True)
			f.write('expected success: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			del self.outcome[:]
			#self.addOutcome(NOTVERIFIED, override=True)

			self.log.info('expecting failure:')
			self.assertEval('len({myString}) == {expectedLength}', expectedLength=1000, myString='a "\n\\ b')
			f.write('expected failure: %s / %s\n'%(LOOKUP[self.getOutcome()], self.getOutcomeReason()))
			#self.addOutcome(NOTVERIFIED, override=True)
			del self.outcome[:]
		
			self.log.info('expecting failure:')
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

		# ensure we don't leak any local variables out into the eval context
		self.assertEval('globals().keys()==locals().keys()')

		# sanity check some of the main symbols are present (both to check match with doc, and for compat with 1.5.0 PySys)
		self.assertEval('os.path and time and math and log and sys and re and io and locale')
		self.assertEval('self.assertEval')
		self.assertEval('OSFAMILY and Project and isstring and pysys and pathexists and pysys.baserunner.BaseRunner and pysys.utils.filegrep')
		self.assertEval("len(import_module('difflib').get_close_matches({word}, ['apple', 'orange', 'applic'])) ==2", word='app')
