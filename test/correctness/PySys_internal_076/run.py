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
		runPySys(self, 'pysys', ['run', '-o', self.output+'/output', '--purge', '-v', 'debug'], workingDir='test')
		runPySys(self, 'pysys-preserveEmptyOutputs', ['run', '-o', self.output+'/output-preserveEmptyOutputs', '--preserveEmptyOutputs', '-v', 'debug'], workingDir='test')
	
			
	def validate(self):
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)')
		
		self.assertPathExists('output/PySys_NestedTestcase/run.log')
		self.assertPathExists('output/PySys_NestedTestcase/nonempty.txt', exists=False)
		self.assertPathExists('output/PySys_NestedTestcase/empty.txt', exists=False)
		
		self.assertPathExists('output/PySys_NestedTestcase/dir1/dir1a/', exists=False) 
		self.assertPathExists('output/PySys_NestedTestcase/dir2/dir2a', exists=False) 
		self.assertPathExists('output/PySys_NestedTestcase/dir2/', exists=False)
		self.assertGrep('pysys.out', ' DEBUG .*Purged empty output directory now that test is complete: .*/PySys_NestedTestcase/dir2'.replace('/', r'[/\\]'))


		self.assertPathExists('output/PySys_NestedTestcaseInspect/run.log')
		self.assertPathExists('output/PySys_NestedTestcaseInspect/nonempty.txt', exists=True)
		self.assertPathExists('output/PySys_NestedTestcaseInspect/empty.txt', exists=False)
		
		self.assertPathExists('output/PySys_NestedTestcaseInspect/dir1/dir1a/', exists=False) # empty so deleted by PySys, but with info logging

		self.assertPathExists('output/PySys_NestedTestcaseInspect/dir2/dir2a', exists=False) # emptied by PySys deleting empty file
		self.assertGrep('pysys.out', ' INFO .*Purged empty output directory now that test is complete: .*/PySys_NestedTestcaseInspect/dir2'.replace('/', r'[/\\]'))
		self.assertPathExists('output/PySys_NestedTestcaseInspect/dir2/', exists=False)

		self.assertPathExists('output-preserveEmptyOutputs/PySys_NestedTestcase/dir2/dir2a/empty.txt')
		self.assertPathExists('output-preserveEmptyOutputs/PySys_NestedTestcase/dir1')
