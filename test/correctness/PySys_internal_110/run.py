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
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys-run', ['run'], workingDir='test', expectedExitStatus='==10')
			
	def validate(self):
		self.assertThatGrep('pysys-run.err', '.*ERROR.*', expected='PYSYS FATAL ERROR: The deprecated project property supportMultipleModesPerRun=false is no longer supported, please update your tests')
