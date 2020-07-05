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

		runPySys(self, 'out-all', ['run', '--mode=ALL', '--record'], workingDir='test')

	def validate(self):

		self.assertDiff('out-all.out', 'ref-out-all.out', includes=[
			' Id +:', 
			'Running with', 'Starting database',
			'Test final outcome:'])
		
		# check the mode shows up ok in the junit report
		self.assertGrep('test/__pysys_junit_xml/TEST-DB_cor_001~MyDatabase_2012.xml', 
			expr='<testsuite .*name="DB_cor_001~MyDatabase_2012"')