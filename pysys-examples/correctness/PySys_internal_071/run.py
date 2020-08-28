import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		self.mkdir(self.output+'/test-exampleproject')
		self.mkdir(self.output+'/test-notset')
		self.copy(self.input+'/NestedTest', self.output+'/test-exampleproject/NestedTest')
		self.copy(self.input+'/NestedTest', self.output+'/test-notset/NestedTest')
		
		shutil.copyfile(self.input+'/pysysproject-notset.xml', self.output+'/test-notset/pysysproject.xml')
		createProjectConfig(self.output+'/test-exampleproject')
		
		for t in ['notset', 'exampleproject']:
			runPySys(self, 'pysys-%s'%t, ['run', '-o', self.output+'/output-%s'%t], workingDir='test-%s'%t, ignoreExitStatus=True)
			self.logFileContents('pysys-%s.out'%t, maxLines=0)
			
	def validate(self):
		# to maintain compatibility with existing pysys projects, if no project option is set we do ignore process failures
		self.assertGrep('pysys-notset.out', expr='Test final outcome:.*PASSED')
		
		# to encourage best practice for new pysys configurations, in the default example configuration file we do not ignore process failures
		self.assertGrep('pysys-exampleproject.out', expr='Test final outcome:.*BLOCKED')
		self.assertGrep('pysys-exampleproject.out', expr='Test outcome reason:.*python-failer-3 returned non-zero exit code 100')
		self.assertGrep('pysys-exampleproject.out', expr='WARN .*python-failer-2 returned exit code 100 [(]expected ==123[)] ... blocked')
		# check we can cope with nonzero expected status - should be INFO not WARN
		self.assertGrep('pysys-exampleproject.out', expr='INFO .*Executed python-failer-1, exit status 100$')

		# quiet mode shoudn't be logged at all
		self.assertGrep('pysys-exampleproject.out', expr='python-failer-quiet', contains=False)

		