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
		runPySys(self, self.output+'/print-full', ['print', '--json'], workingDir=self.input+'/dir1')
		runPySys(self, self.output+'/print-moved-root', ['print', '--full'], workingDir=self.input+'/dir1', projectfile=self.output+'/pysysproject.xml')
			
	def validate(self):
		# check none of the dir descriptors affected anything if the project root dir was not a parent 
		# of the test dir
		self.assertGrep('print-moved-root.out', expr='Test groups:.*root-group', contains=False)
		self.assertGrep('print-moved-root.out', expr='Test groups:.*dir2-group', contains=False)

		self.logFileContents('print-full.out', maxLines=0)

		self.assertDiff('print-full.out', 'ref-print-full.out', replace=[
			('"[^"]+PySys_internal_104', '"<path-to-test>/PySys_internal_104'), # snip out absolute paths
			(r'[\\]','/'),
			('//','/'),
			(', *$', ','), # python 2 vs 3 have slightly different pretty JSON formatting
			])
			
		with open(self.output+'/print-full.out', 'rb') as f:
			if sys.version_info[:2] != (3, 5): # 3.x before 3.6 didn't support reading binary
				self.assertTrue(json.load(f)!=None) # check it's valid JSON - would throw if not