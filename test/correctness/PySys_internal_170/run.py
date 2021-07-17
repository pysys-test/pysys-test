import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/pysys-output'], workingDir=self.input)

	def validate(self):
		self.logFileContents('pysys-run.out')
		
		self.assertGrep('pysys-output/UnpackingTest/zipoutput/ParentDir/MyFile1.txt', 'AAAA BBBB')
		self.assertGrep('pysys-output/UnpackingTest/xzoutput/MyFile1.txt', 'AAAA BBBB')
		
		# Others should have been auto-cleaned up
		self.assertPathExists('pysys-output/UnpackingTest/MyFile1.txt', exists=False)
		self.assertPathExists('pysys-output/UnpackingTest/archive', exists=False)