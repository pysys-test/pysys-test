import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '--record', '--threads', '2', '-o', 'pysys-output'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		# ensure these appear at start of the line, which for some CI writers is important
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		