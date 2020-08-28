import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, os.path.join(self.output,'test'))

		p = runPySys(self, 'pysys', ['run', '-o', os.path.join(self.output,'myoutdir'), '--progress', '--cycle', '2'], workingDir='test', ignoreExitStatus=True)
		self.assertThat('%d > 0', p.exitStatus)
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)

		self.assertGrep('pysys.out', expr="runner object str='BaseRunner'")
		self.assertGrep('pysys.out', expr="NestedPass test object str='NestedPass.cycle001'")
		self.assertGrep('pysys.out', expr="NestedPass test object str='NestedPass.cycle002'")


		self.assertOrderedGrep('pysys.out', exprList=[
			'INFO.*Test progress: completed 1/6 = 16.7% of tests in ',
			'1 FAILED',
			'Test progress: completed 2/6'
		])
		self.assertOrderedGrep('pysys.out', exprList=[
			'INFO.*Test progress: completed 4/6 = 66.7% of tests',
			'  1 PASSED [(]25[.]0%[)]',
			'  1 TIMED OUT, 2 FAILED',
			'Recent failures: ',
			'  FAILED: NestedFail \\[CYCLE 01\\]',
			'  TIMED OUT: NestedTimedout \\[CYCLE 01\\]: Reason for timed out outcome is general tardiness',
			'  FAILED: NestedFail \\[CYCLE 02\\]',
			'Test progress: completed 5/6'
		])
		self.assertOrderedGrep('pysys.out', exprList=[
			'Summary of failures: ',
			'List of failed test ids:',
			'CRIT .* NestedTimedout NestedFail$'
			])