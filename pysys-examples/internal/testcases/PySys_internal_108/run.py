import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		e = runPySys(self, self.output+'/print', ['print'], workingDir=self.input, ignoreExitStatus=True).exitStatus
		self.assertThat('%d != 0', e)
		
		runPySys(self, self.output+'/print-allow', ['print'], workingDir=self.input, environs={'PYSYS_ALLOW_DUPLICATE_IDS':'true'})
					
	def validate(self):
		self.assertGrep('print.err', expr='ERROR: Found 2 duplicate descriptor ids: My_Test - in .+dir1.+pysystest.xml and .+dir2.+pysystest.xml')
		self.assertGrep('print.err', expr='My_Test - in .+dir1.+pysystest.xml and .+dir3.+pysystest.xml')
		