import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, os.path.join(self.output,'test'))

		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		p = runPySys(self, 'pysys', ['run', '-o', os.path.join(self.output,'myoutdir'), '--progress', '--cycle', '2'], workingDir='test', ignoreExitStatus=True)
		self.assertThat('%d > 0', p.exitStatus)
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)

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
