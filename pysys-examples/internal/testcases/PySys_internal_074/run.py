import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

from pysys.utils.filecopy import filecopy

if PROJECT.rootdir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.rootdir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		filecopy(PROJECT.rootdir+'/pysysproject.xml', self.output+'/pysysproject.xml')
		runPySys(self, 'make', ['make', 'mynewtest'])
		runPySys(self, 'run', ['run','mynewtest'])
			
	def validate(self):
		self.assertGrep('make.err', expr='.*', contains=False) # no errors
		
		self.assertThat('os.path.isdir(%s)', repr(self.output+'/mynewtest/Input'))
		self.assertThat('os.path.isfile(%s)', repr(self.output+'/mynewtest/pysystest.xml'))
		self.assertThat('os.path.isfile(%s)', repr(self.output+'/mynewtest/run.py'))
	
		# check for correct default outcome for new tests
		self.assertGrep('run.out', expr='Test final outcome *:.*NOT VERIFIED') 
		self.assertGrep('run.out', expr='mynewtest') 
		