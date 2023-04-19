import time
from pysys.config.descriptor import TestDescriptor
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.utils.fileutils import toLongPathSafe

class PySysTest(BaseTest):
	def execute(self):
		# cheekily take advantage of this to report an unplanned test result directly using the runner:
		descr = TestDescriptor(
			self.input+'/MyDynamicUnplannedTestDirNonexistent/testfile.py',
			'MyDynamicUnplannedTest',
			testDir=toLongPathSafe(self.input+'/MyDynamicUnplannedTestDirNonexistent'), # make sure this doesn't break anything
			output=toLongPathSafe(self.input+'/MyDynamicUnplannedTestDirNonexistent-OUTPUT'), # make sure this doesn't break anything
		)
		descr.mode = None # have to hack this for now, since basetest complains otherwise
		faketest = BaseTest(descr, self.runner.outsubdir, self.runner)
		faketest.addOutcome(FAILED, "Extra result from fake test")
		if self.testCycle == 1:
			self.runner.reportTestOutcome(faketest, time.time(), 5.6, runLogOutput='MyRunLogOutput')

		self.addOutcome(PASSED)
		self.startPython([self.input+'/hello.py'], stdouterr='hello') # just to generate some code coverage
		self.reportPerformanceResult(123, 'A performance key', '/s')
		
		self.runner.publishArtifact(self.output+'/run.log', category='MyCustomCategory')
		
	def validate(self):
		pass 
