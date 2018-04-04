import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')

		env = dict(os.environ)
		env['PYSYS_COLOR'] = 'tRue'
		env['PYSYS_TEST_FRIENDLY_ESCAPES'] = 'true'
		p = self.startProcess(command=sys.executable,
			arguments = [[a for a in sys.argv if a.endswith('pysys.py')][0], 'run', '-o', self.output+'/myoutdir', '-v', 'DEBUG'],
			environs = env, workingDir='test',
			stdout = 'pysys.out', stderr='pysys.err', displayName='pysys', 
			ignoreExitStatus=False, abortOnError=True)
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.out', expr=r'Failed to format log message', contains=False)
		self.assertDiff('pysys.out', 'pysys.out', includes=['reason', 'Sample message', 'outcome', 'Id', 'Title', 'FAILED', 'My exception', 'Traceback'])
		
		# check run.log not affected
		self.assertGrep('myoutdir/PySys_NestedTestcase/run.log', expr=r'INFO +skipped reason message ... skipped')
