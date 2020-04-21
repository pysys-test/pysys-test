import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, self.output+'/print-full', ['print', '--full'], workingDir=self.input)
		runPySys(self, 'pysys-run', ['run', '-o', self.output+'/test'], workingDir=self.input)
					
	def validate(self):
		self.assertGrep('print-full.out', expr='Test skip reason: *Skipped by pysystest.xml')
		self.assertGrep('print-full.out', expr='Test skip reason: *Skipped by dirconfig')
		
		self.assertGrep('pysys-run.out', expr='Test outcome reason: *Skipped by pysystest.xml')
		self.assertGrep('pysys-run.out', expr='Test outcome reason: *Skipped by dirconfig')
		