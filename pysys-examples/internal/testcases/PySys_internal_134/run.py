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
		shutil.copyfile(self.input+'/pysysproject.xml', self.output+'/pysysproject.xml')
		runPySys(self, self.output+'/print', ['print'], workingDir=self.input)
			
	def validate(self):
		self.assertGrep('print.out', expr='PySysTest')
		self.assertGrep('print.out', expr='DescXML')
