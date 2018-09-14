# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')

		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		# use multiple cycles since the buffering is different
		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir'], workingDir=self.output+'/test', ignoreExitStatus=True)
		self.logFileContents('pysys.out', maxLines=0)
		self.logFileContents('pysys.err', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)
		# we assume test 1 runs first
		self.assertOrderedGrep('pysys.out', exprList=['Test1:', 'Test2:'])

		self.assertGrep('pysys.out', expr='Test2: Test2Symbol is defined')
		self.assertGrep('pysys.out', expr='Test2: Test1Symbol is not defined')
		self.assertGrep('pysys.out', expr='Test2: io module is not imported')
		self.assertGrep('pysys.out', expr='Test2: log is not imported')
		
		return
		self.assertGrep('pysys.out', expr='Test final outcome:.*FAILED')
		