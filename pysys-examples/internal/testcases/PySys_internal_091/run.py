import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil
from pysys.utils.pycompat import PY2

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		
		# use multiple cycles since the buffering is different
		try:
			runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir'], workingDir=self.output+'/test', environs={'PYSYS_COLOR':'true'})
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)

		self.assertOrderedGrep('myoutdir/NestedTest/run.log', exprList=[
			'About to print', 
			'INFO .*Hello world! unicode plain',
			'Hello world! bytes plain',
			'Hello %s',
			'INFO',
			'INFO',
			'After newlines'
		], encoding='utf-8')
		
		self.assertGrep('myoutdir/NestedTest/run.log', expr=u'Hello world! . bytes' if PY2 else u'Hello world! \xa3', encoding='utf-8')
