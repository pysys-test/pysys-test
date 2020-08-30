import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		self.copy(self.input, self.output+'/test')

		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '--cycle', '10', '-n', '20'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		greps = []
		for i in range(1, 11):
			greps.append('Cycle.*: *%d'%i)
			greps.append('====')
			greps.append('Called BaseRunner.cycleComplete for cycle %d'%i)
		self.assertOrderedGrep('pysys.out', exprList=greps)
