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

		exitcode = runPySys(self, 'pysys', ['run'], ignoreExitStatus=True, workingDir='test')
		self.assertThat('%d != 0', exitcode.exitStatus)
		self.logFileContents('pysys.out', maxLines=0)
		self.logFileContents('pysys.err')
			
	def validate(self):
		self.assertGrep('pysys.err', expr='Traceback')
		self.assertGrep('pysys.err', expr='customfmt.py')
		self.assertGrep('pysys.err', expr='this is a syntax error!')