import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')

		env = dict(os.environ)
		env.pop('PYSYS_COLOR','')
		env.pop('PYSYS_PROGRESS','')
		p = self.startProcess(command=sys.executable,
			arguments = [[a for a in sys.argv if a.endswith('pysys.py')][0], 'run', '-o', self.output+'/myoutdir', '--progress', '--cycle', '2'],
			environs = env, workingDir='test',
			stdout = 'pysys.out', stderr='pysys.err', displayName='pysys', 
			ignoreExitStatus=False, abortOnError=True)
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)

		self.assertOrderedGrep('pysys.out', exprList=[
			'INFO.*--- Progress: completed 1/6 = 16.7% of tests in ',
			'1 FAILED',
			'--- Progress: completed 2/6'
		])
		self.assertOrderedGrep('pysys.out', exprList=[
			'INFO.*--- Progress: completed 4/6 = 66.7% of tests',
			'  1 PASSED [(]25[.]0%[)]',
			'  1 TIMED OUT, 2 FAILED',
			'Recent failures: ',
			'  FAILED: NestedFail \\[CYCLE 01\\]',
			'  TIMED OUT: NestedTimedout \\[CYCLE 01\\]: Reason for timed out outcome is general tardiness',
			'  FAILED: NestedFail \\[CYCLE 02\\]',
			'--- Progress: completed 5/6'
		])

