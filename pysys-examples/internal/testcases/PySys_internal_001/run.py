from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 
import shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')
		try:
			runPySys(self, 'pysys', ['run', '-o', 'myoutdir', 
				'-X', 'projectbooloverride=fAlse', 
				'-X', 'cmdlineoverride=tRue'], workingDir='test', environs={
				'TEST_USER':"Felicity Kendal"
			})
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err')
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)

	def validate(self):
		# mostly checked by nested testcase, but also:
		self.assertGrep('pysys.out', expr='projectbool=True')
		self.assertGrep('pysys.out', expr='projectbooloverride=False')
		self.assertGrep('pysys.out', expr='booldeftrue=True')
		self.assertGrep('pysys.out', expr='booldeffalse=False')
		self.assertGrep('pysys.out', expr='cmdlineoverride=True')
		