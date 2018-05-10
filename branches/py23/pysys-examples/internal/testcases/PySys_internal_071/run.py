import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		
		self.mkdir(self.output+'/test-exampleproject')
		self.mkdir(self.output+'/test-notset')
		shutil.copytree(self.input+'/NestedTest', self.output+'/test-exampleproject/NestedTest')
		shutil.copytree(self.input+'/NestedTest', self.output+'/test-notset/NestedTest')
		
		shutil.copyfile(self.input+'/pysysproject-notset.xml', self.output+'/test-notset/pysysproject.xml')
		shutil.copyfile(self.input+'/../../../../pysysproject.xml', self.output+'/test-exampleproject/pysysproject.xml')
		
		env = dict(os.environ)
		env.pop('PYSYS_COLOR','')
		env.pop('PYSYS_PROGRESS','')
		for t in ['notset', 'exampleproject']:
			p = self.startProcess(command=sys.executable,
				arguments = [os.path.abspath([a for a in sys.argv if a.endswith('pysys.py')][0]), 
					'run', '-o', self.output+'/output-%s'%t],
				environs = env, workingDir='test-%s'%t,
				stdout = 'pysys-%s.out'%t, stderr='pysys-%s.err'%t, displayName='pysys '+t, 
				ignoreExitStatus=True, abortOnError=True, state=FOREGROUND)
			self.logFileContents('pysys-%s.out'%t, maxLines=0)
			
	def validate(self):
		# to maintain compatibility with existing pysys projects, if no project option is set we do ignore process failures
		self.assertGrep('pysys-notset.out', expr='Test final outcome:.*PASSED')
		
		# to encourage best practice for new pysys configurations, in the default example configuration file we do not ignore process failures
		self.assertGrep('pysys-exampleproject.out', expr='Test final outcome:.*BLOCKED')
		self.assertGrep('pysys-exampleproject.out', expr='Test failure reason:.*python failer returned non-zero exit code 100')
