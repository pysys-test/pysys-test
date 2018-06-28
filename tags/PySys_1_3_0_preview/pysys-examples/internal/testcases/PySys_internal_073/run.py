import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

class PySysTest(BaseTest):

	def execute(self):
		testsdir = os.path.normpath(self.input+'/../../../..')
		assert testsdir.endswith('pysys-examples'), testsdir
		self.log.info('printing tests from: %s', testsdir)
		
		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		runPySys(self, 'basic', ['print'], workingDir=testsdir)
		runPySys(self, 'thistest', ['print', 'PySys_internal_073'], workingDir=testsdir)
		runPySys(self, 'full', ['print', '--full'], workingDir=testsdir)
		runPySys(self, 'groups', ['print', '--groups'], workingDir=testsdir)
		runPySys(self, 'modes', ['print', '--modes'], workingDir=testsdir)
		runPySys(self, 'nonexistent', ['print', 'non-existent'], workingDir=testsdir, ignoreExitStatus=True)
		runPySys(self, 'emptydir', ['print'], workingDir=self.mkdir('emptydir'), ignoreExitStatus=True)
			
	def validate(self):
		for t in ['basic', 'thistest', 'full', 'groups', 'modes']:
			self.assertGrep(t+'.err', expr='.*', contains=False) # no errors

		self.assertGrep('basic.out', expr='Fibonacci_test_001 *: *[^ ]+')
		self.assertGrep('full.out', expr='Test id *: *Fibonacci_test_001') # just pick one example
		self.assertGrep('modes.out', expr='mode1') # just pick one example
		self.assertLineCount('thistest.out', expr='.', condition='==1')
		
		self.assertGrep('groups.out', expr='examples') # just pick one example

		self.assertGrep('emptydir.err', expr='The supplied options did not result in the selection of any tests')
		self.assertGrep('nonexistent.err', expr='Unable to locate requested testcase')
