from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.reasons = []
		# straight diff
		self.copy(self.input+'/file1.txt', 'file1.txt')
		self.assertDiff(file1='file1.txt')

		self.assertDiff(file1='file1.txt', file2='file1_with_whitespace.txt')
		self.checkForFailedOutcome()
		
		# override project/test property; should now pass
		self.defaultAssertDiffStripWhitespace = True
		self.assertDiff(file1='file1.txt', file2='file1_with_whitespace.txt')
		
		# diff with an ignores
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', ignores=[r'\(on my Vespa 300 GTS ...\)'])
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', ignores=['Vespa'])
		
		self.copy(self.input+'/file2.txt', 'file2.txt')
		self.assertDiff(file1='file2.txt', file2='ref_file.txt', ignores=[r'\(on my Vespa 250 GTS ...\)', 'somenonexistentexpression'])
		self.checkForFailedOutcome()
	
		# diff with some includes
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', includes=['Now', 'Waiving', 'foobarbaz'])

		self.assertDiff(file1='file3.txt', filedir1=self.input, file2='ref_file.txt', includes=['Now', 'moon', 'foobarbaz'])
		self.checkForFailedOutcome()
	
		# dif with a sort 
		self.assertDiff(file1='file3.txt', filedir1=self.input, file2='ref_file.txt', sort=True)

		# use a replace
		self.assertDiff(file1='file4.txt', filedir1=self.input, file2='ref_file.txt', replace=[('navel','charmer')])

		self.assertGrep('file2.txt.diff', expr='+(on my Vespa 300 GTS', literal=True)
		
		# check we indicate the directory that they're in
		self.assertGrep('run.log', expr=r'File comparison between file1.txt and Reference[/\\]file1.txt ... passed')
		self.assertGrep('file2.txt.diff', expr='--- Reference.ref_file.txt')
		self.assertGrep('file2.txt.diff', expr=r'\+\+\+ Output.+file2.txt')
		
		self.assertThat('expected in outcomeReasons', 
			outcomeReasons=sorted(self.reasons),
			expected=r'File comparison between file1.txt and Reference/file1_with_whitespace.txt: "+The moorcock springs on whirring wings among the blooming heather," "-   The moorcock springs on whirring wings among the blooming heather," "+Waiving grain wide over the plain delights the weary farmer," ...')
			

	def checkForFailedOutcome(self):
		self.log.info('(expected failed outcome) Failure outcome: "%s"'%self.getOutcomeReason())
		self.reasons.append(self.getOutcomeReason().replace('Reference\\', 'Reference/')) # platform normalization
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED, 'did not get expected failure', abortOnError=True)
		self.log.info('')
		
		
