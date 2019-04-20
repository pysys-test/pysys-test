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
		shutil.copytree(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '-o', self.output+'/output', '--purge', '-v', 'debug'], workingDir='test')
	
			
	def validate(self):
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)')
		
		self.assertPathExists('output/PySys_NestedTestcase/run.log')
		self.assertPathExists('output/PySys_NestedTestcase/nonempty.txt', exists=False)
		self.assertPathExists('output/PySys_NestedTestcase/empty.txt', exists=False)
		self.assertPathExists('output/PySys_NestedTestcase/dir1', exists=False)
		self.assertPathExists('output/PySys_NestedTestcase/dir2', exists=False)
