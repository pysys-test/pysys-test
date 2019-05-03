import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, 'pysys-run', ['run', '-G', '(eSt01|contains r.gex pattern)', '-o', self.output+'/test'], workingDir=self.input)
		runPySys(self, 'pysys-print', ['print', '--grep', '(eSt01|contains r.gex pattern)'], workingDir=self.input)
			
	def validate(self):
		for f in ['pysys-run.out', 'pysys-print.out']:
			self.assertGrep(f, expr='Test01')
			self.assertGrep(f, expr='Test02', contains=False)
			self.assertGrep(f, expr='Test03')
			