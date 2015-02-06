from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines bright')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines right')
		self.checkForFailedOutcome()
		print
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon shines right', contains=False)
		self.assertGrep(file='file.txt', filedir=self.input, expr='(?P<tag>moon) shines bright')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright')
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright', ignores=['oon'], contains=False)
		self.assertGrep(file='file.txt', filedir=self.input, expr='moon.*bright', ignores=['pysys is great', 'oh yes it is'])
		self.assertGrep(file='file.txt', filedir=self.input, expr='Now eastlin|westlin winds')
		
	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
