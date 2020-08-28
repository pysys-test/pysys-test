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
		self.copy(self.input+'/MyTest', self.output+'/MyTest')
		runPySys(self, self.output+'/print-without-dirconfig', ['print', '--json'], workingDir=self.output, defaultproject=True)
		
		self.copy(os.path.dirname(pysys.__file__)+'/xml/templates/dirconfig/default.xml', self.output+'/pysysdirconfig.xml')
		runPySys(self, self.output+'/print-with-dirconfig', ['print', '--json'], workingDir=self.output)
			
	def validate(self):
		# if it worked, the dir config will have made no difference
		self.assertDiff(self.output+'/print-without-dirconfig.out', self.output+'/print-with-dirconfig.out')