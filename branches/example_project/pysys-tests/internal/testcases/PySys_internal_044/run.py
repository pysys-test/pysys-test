from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		# straight diff
		self.assertDiff(file1='file1.txt', filedir1=self.input, file2='ref_file.txt')
		
		# diff with an ignores
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', ignores=['\(on my Vespa 300 GTS ...\)'])
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', ignores=['Vespa'])
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', ignores=['\(on my Vespa 250 GTS ...\)'])
		self.checkForFailedOutcome()
	
		# diff with an includes
		self.assertDiff(file1='file2.txt', filedir1=self.input, file2='ref_file.txt', includes=['Now'])
	
		# dif with a sort 
		self.assertDiff(file1='file3.txt', filedir1=self.input, file2='ref_file.txt', sort=True)

		# use a replace
		self.assertDiff(file1='file4.txt', filedir1=self.input, file2='ref_file.txt', replace=[('navel','charmer')])

		self.assertGrep('file2.txt.diff', expr='+(on my Vespa 300 GTS', literal=True)

	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		