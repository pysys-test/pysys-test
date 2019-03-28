import os, sys, re, shutil
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.rootdir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.rootdir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, 'toplevel', ['--help'], defaultproject=True)
		runPySys(self, 'run', ['run', '--help'], defaultproject=True)
		runPySys(self, 'print', ['print', '-h'], defaultproject=True)
		runPySys(self, 'make', ['make', '--help'], defaultproject=True)
			
	def validate(self):
		for t in ['toplevel', 'run', 'print', 'make']:
			self.assertGrep(t+'.err', expr='.', contains=False)
			self.assertGrep(t+'.out', expr='Exception', contains=False)
			self.assertGrep(t+'.out', expr='.') # check not empty
			self.assertGrep(t+'.out', expr='.'*(120+1), contains=False) # check no lines are too long
