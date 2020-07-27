import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, json

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, self.output+'/pysys', ['run', '-o', self.output+'/pysys_output'], workingDir=self.input, expectedExitStatus='!=0')

	def validate(self):
		self.assertLineCount('pysys_output/Default/run.log', 'Traceback', condition='==1')
		self.assertGrep('pysys_output/IgnoreErrors/run.log', 'WARN .*Error while running cleanup function [(]ignoreErrors=True[)]: ')
		self.assertGrep('pysys_output/IgnoreErrors/run.log', 'Test final outcome: .*NOT VERIFIED')
		self.assertGrep('pysys_output/Default/run.log', 'Test final outcome: .*BLOCKED')
		self.assertGrep('pysys_output/Default/run.log', 'Test outcome reason: .*Cleanup failed with 1 errors: Cleanup function failed: My cleanup function error [(]Exception[)]')
