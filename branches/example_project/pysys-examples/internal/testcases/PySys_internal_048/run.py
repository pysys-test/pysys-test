from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['moon shines bright'])
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['moon shines right'])
		self.checkForFailedOutcome()
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['moon shines right'], contains=False)
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['(?P<tag>moon) shines bright'])
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['moon.*bright'])
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=['Now eastlin|westlin winds'])
		
		exprList=[]
		exprList.append('(?P<direction>westlin|eastlin)')
		exprList.append('moon shines bright')
		exprList.append('my charmer')			
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=exprList)
		
		exprList=[]
		exprList.append('(?P<direction>northlin|eastlin)')
		exprList.append('moon shines bright')
		exprList.append('my charmer')			
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=exprList)
		self.checkForFailedOutcome()
		
		
	def checkForFailedOutcome(self):
		outcome = self.outcome.pop()
		if outcome == FAILED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
