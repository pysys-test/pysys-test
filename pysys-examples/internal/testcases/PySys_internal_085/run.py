# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob
import locale

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.log.info('Preferred encoding = %s, test string = %s', locale.getpreferredencoding(), TEST_STR)
		if locale.getpreferredencoding() in ['ANSI_X3.4-1968', 'ascii']: self.skipTest('cannot run in ASCII locale')

		self.copy(self.input, self.output+'/test')

		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '--record', '--cycle', '2', '-n', '2'], ignoreExitStatus=True, workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)
		self.assertGrep('pysys.err', expr='WARN.*', contains=False)

		# pysys.out will be in the default encoding
		self.assertGrep('pysys.out', expr='Reason for timed out outcome is general tardiness - %s'%TEST_STR, encoding=locale.getpreferredencoding())
