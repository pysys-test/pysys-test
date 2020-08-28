from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		if not IS_WINDOWS: self.skipTest('Only runs on Windows')

	def validate(self):
		self.assertEval('{inputDir}[0] == {inputDir}[0].upper()', inputDir=self.input)
		self.assertEval('{outputDir}[0] == {outputDir}[0].upper()', outputDir=self.output)
		self.assertEval('{referenceDir}[0] == {referenceDir}[0].upper()', referenceDir=self.reference)
