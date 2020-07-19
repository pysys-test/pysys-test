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
		runPySys(self, self.output+'/pysys', ['run', '-o', self.output+'/pysys_output'], workingDir=self.input)

	def validate(self):
		self.assertGrep('pysys.out', expr='Python reported 2 warnings during execution of tests.*')
		self.assertGrep('pysys_output/PySysTest/run.log', expr='WARN *Python reported a warning: .*This is simulated warning 1')
