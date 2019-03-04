# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob
import locale

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 

class PySysTest(BaseTest):

	def execute(self):
		
		if locale.getpreferredencoding() in ['ANSI_X3.4-1968', 'ascii']: self.skipTest('cannot run in ASCII locale')

		shutil.copytree(self.input, self.output+'/test')

		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '--record', '--cycle', '2', '-n', '2'], ignoreExitStatus=True)
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)
		self.assertGrep('pysys.err', expr='WARN.*', contains=False)

		# pysys.out will be in the default encoding
		self.assertGrep('pysys.out', expr='Reason for timed out outcome is general tardiness - %s'%TEST_STR, encoding=locale.getpreferredencoding())
