import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')

		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read()) # define runPySys
		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '--cycle', '10', '-n', '20'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		greps = []
		for i in range(1, 11):
			greps.append('Cycle.*: *%d'%i)
			greps.append('====')
			greps.append('Called BaseRunner.cycleComplete for cycle %d'%i)
		self.assertOrderedGrep('pysys.out', exprList=greps)
