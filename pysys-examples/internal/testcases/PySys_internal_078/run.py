import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']

		shutil.copytree(self.input, self.output+'/test')
		runPySys(self, 'all', ['print'], workingDir='test')
		runPySys(self, 'full', ['print', '--full'], workingDir='test')
		runPySys(self, 'include', ['print', '--include', 'group1', '--include', 'group2'], workingDir='test')
		runPySys(self, 'exclude', ['print', '--exclude', 'group3', '--exclude', 'group4'], workingDir='test')
		runPySys(self, 'ranges', ['print', ':1', '3:04', '007:'], workingDir='test')
		runPySys(self, 'type', ['print', '--type', 'manual'], workingDir='test')	
		# currently trace only works on its first argument, not sure if that's intended or not
		runPySys(self, 'trace', ['print', '--trace', 'requirement-1', '--trace', 'requirement-2'], workingDir='test')	
		
	def validate(self):
		for f in ['all.out', 'include.out', 'exclude.out', 'ranges.out', 'type.out', 'trace.out']:
			self.assertDiff(f, f)
