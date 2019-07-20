import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		# use root pysys project so we can check all our own tests print ok
		# it's safe to use project root because we are not enabling record mode
		testsdir = os.path.normpath(PROJECT.testRootDir)
		
		assert testsdir.endswith('pysys-examples'), testsdir
		self.log.info('printing tests from: %s', testsdir)
		
		runPySys(self, 'basic', ['print'], workingDir=testsdir)
		runPySys(self, 'sort-by-id', ['print', '--sort', 'id'], workingDir=testsdir) # just check for no exceptions, no validation
		runPySys(self, 'sort-by-title', ['print', '--sort', 'title'], workingDir=testsdir) # just check for no exceptions, no validation
		runPySys(self, 'thistest', ['print', 'PySys_internal_073'], workingDir=testsdir)
		runPySys(self, 'full', ['print', '--full'], workingDir=testsdir)
		runPySys(self, 'groups', ['print', '--groups'], workingDir=testsdir)
		runPySys(self, 'modes', ['print', '--modes'], workingDir=testsdir)
		runPySys(self, 'requirements', ['print', '--requirements'], workingDir=testsdir)
		runPySys(self, 'nonexistent', ['print', 'non-existent'], workingDir=testsdir, ignoreExitStatus=True)
		runPySys(self, 'emptydir', ['print'], workingDir=self.mkdir('emptydir'), ignoreExitStatus=True, 
			projectfile=PROJECT.testRootDir+'/pysysproject.xml')
			
	def validate(self):
		for t in ['basic', 'thistest', 'full', 'groups', 'modes']:
			self.assertGrep(t+'.err', expr='.*', contains=False) # no errors

		self.assertGrep('basic.out', expr='Fibonacci_test_001 *[|] *[^ ]+')
		self.assertGrep('full.out', expr='Test id *: *Fibonacci_test_001') # just pick one example
		self.assertGrep('modes.out', expr='FibonacciMode1') # just pick one example
		self.assertLineCount('thistest.out', expr='.', condition='==1')
		
		self.assertGrep('groups.out', expr='examples') # just pick one example
		self.assertGrep('requirements.out', expr='AL1') # just pick one example

		self.assertGrep('emptydir.err', expr='The supplied options did not result in the selection of any tests')
		self.assertGrep('nonexistent.err', expr='Unable to locate requested testcase')
