import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, self.output+'/test')

		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read()) # define runPySys
		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '-v', 'DEBUG'], workingDir='test', ignoreExitStatus=True, 
			environs={
				'PYSYS_COLOR': 'tRue',
				'PYSYS_TEST_FRIENDLY_ESCAPES': 'true',
			})
		
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.out', expr=r'Failed to format log message', contains=False)
		self.assertDiff('pysys.out', 'pysys.out', includes=['reason', 'Sample message', 'outcome', 'Id', 'Title', 'FAILED', 'My exception', 'Traceback'])
		
		# check run.log not affected
		self.assertGrep('myoutdir/PySys_NestedTestcase/run.log', expr=r'INFO +skipped reason message ... skipped')
