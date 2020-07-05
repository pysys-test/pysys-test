import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, io

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')

		runPySys(self, 'pysys-print-full', ['print', '--full'], workingDir='test')
		runPySys(self, 'pysys-print', ['print'], workingDir='test')
		runPySys(self, 'pysys-run', ['run', '--mode', 'ALL'], workingDir='test')

	def validate(self):
		self.assertDiff('pysys-print.out', 'ref-pysys-print.out')
		self.assertGrep('pysys-run.out', expr='Id *: *MyTest')
		self.assertGrep('pysys-run.out', expr='Id *: *dirprefix_MyCustomTest_002~MyMode1')
		self.assertGrep('pysys-run.out', expr='Id *: *dirprefix_MyCustomTest_002~MyMode2')
		self.assertGrep('pysys-run.out', expr='Id *: *dirprefix_PySys_cor_001')
