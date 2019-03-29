import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re
from pysys.utils.filecopy import filecopy
from pysys.xml.project import createProjectConfig

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		createProjectConfig(self.output)
		runPySys(self, 'make1', ['make', 'mynewtest1'])
		runPySys(self, 'make2', ['make', 'mynewtest2'])
		runPySys(self, 'run1', ['run', '-o', 'cleaned'])
		runPySys(self, 'run2', ['run', '-o', 'notcleaned'])
		runPySys(self, 'clean', ['clean', '-o', 'cleaned', '--all', 'mynewtest1'])
			
	def validate(self):
		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest1/Output/notcleaned/run.log'))
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/Output/cleaned/run.log'))

		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest2/Output/notcleaned/run.log'))
		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest2/Output/cleaned/run.log'))

		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/run.pyc')) # python2
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/__pycache__')) # python3
