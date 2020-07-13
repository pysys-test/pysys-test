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
		runPySys(self, self.output+'/pysys-info', ['run', '-vpython:myloggercat=info'], workingDir=self.input)
		runPySys(self, self.output+'/pysys-debug', ['run', '-vpython:myloggercat=debug'], workingDir=self.input)

	def validate(self):
		self.logFileContents('pysys-debug.out', includes=['Hello at .*'])
		self.assertGrep('pysys-debug.out', expr='Hello at debug')
		self.assertGrep('pysys-info.out', expr='Hello at debug', contains=False)
		self.assertGrep('pysys-info.out', expr='Hello at info')
