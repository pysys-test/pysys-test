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
		runPySys(self, 'all', ['print'], workingDir='test')
		runPySys(self, 'full', ['print', '--full'], workingDir='test')
		runPySys(self, 'include', ['print', '--include', 'group1', '--include', 'group2'], workingDir='test')
		runPySys(self, 'exclude', ['print', '--exclude', 'group3', '--exclude', 'group4'], workingDir='test')
		runPySys(self, 'ranges', ['print', ':1', '3:04', '00007:'], workingDir='test')
		runPySys(self, 'suffix-ranges', ['print', ':test_01', 'test_03:est_04', 'test_07:'], workingDir='test')
		runPySys(self, 'type', ['print', '--type', 'manual'], workingDir='test')	
		# currently trace only works on its first argument, not sure if that's intended or not
		runPySys(self, 'trace', ['print', '--trace', 'requirement-1', '--trace', 'requirement-2'], workingDir='test')	
		
	def validate(self):
		for f in ['all.out', 'include.out', 'exclude.out', 'ranges.out',  'suffix-ranges.out', 'type.out', 'trace.out']:
			self.assertDiff(f, f)
