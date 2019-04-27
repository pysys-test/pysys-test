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
		shutil.copyfile(self.input+'/pysysproject.xml', self.output+'/pysysproject.xml')
		runPySys(self, self.output+'/print-full', ['print', '--full'], workingDir=self.input+'/dir1')
		runPySys(self, self.output+'/print-moved-root', ['print', '--full'], workingDir=self.input+'/dir1', projectfile=self.output+'/pysysproject.xml')
			
	def validate(self):
		# check none of the dir descriptors affected anything if the project root dir was not a parent 
		# of the test dir
		self.assertGrep('print-moved-root.out', expr='Test groups:.*root-group', contains=False)
		self.assertGrep('print-moved-root.out', expr='Test groups:.*dir2-group', contains=False)

		self.logFileContents('print-full.out', maxLines=0)

		self.assertDiff('print-full.out', 'ref-print-full.out', replace=[
			(': .*PySys_internal_104', ': <path-to-test>/PySys_internal_104'), # snip out absolute paths
			(r'[\\]','/'),
			])