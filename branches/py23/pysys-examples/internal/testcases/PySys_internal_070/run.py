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
			arguments = [os.path.abspath([a for a in sys.argv if a.endswith('pysys.py')][0]), 
				'run', '-o', self.output+'/myoutdir', '--cycle', '10', '-n', '20'],
			environs = env, workingDir='test',
			stdout = 'pysys.out', stderr='pysys.err', displayName='pysys', 
			ignoreExitStatus=False, abortOnError=True, state=FOREGROUND)
		self.logFileContents('pysys.out', maxLines=0)
			
	def validate(self):
		greps = []
		for i in range(1, 11):
			greps.append('Cycle.*: *%d'%i)
			greps.append('====')
			greps.append('Called BaseRunner.cycleComplete for cycle %d'%i)
		self.assertOrderedGrep('pysys.out', exprList=greps)
