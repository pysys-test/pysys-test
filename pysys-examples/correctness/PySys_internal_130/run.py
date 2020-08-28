import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, zipfile, glob

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/testroot')
	
		runPySys(self, 'pysys', ['run', '-Xparam1=cmd line'],
		environs={
			'PYSYS_DEFAULT_ARGS':'"-Xparam1=env var" -Xparam2="env var" -j x2.5'
		}, workingDir='testroot')
						
	def validate(self):
		self.assertGrep('pysys.out', expr=r'param1="cmd line"') # cmd line takes precedence over env var
		self.assertGrep('pysys.out', expr=r'param2="env var"') # env var works, including with spaces
