import os, sys, re, shutil
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		# should NOT need a project to display top-level usage
		runPySys(self, 'noargs', [], projectfile='non-existent-project')
		runPySys(self, 'toplevel', ['--help'], projectfile='non-existent-project')
		runPySys(self, 'makeproject', ['makeproject', '--help'], projectfile='non-existent-project')
		
		# these options all do need a project
		runPySys(self, 'run', ['run', '--help'], defaultproject=True)
		runPySys(self, 'print', ['print', '-h'], defaultproject=True)
		runPySys(self, 'make', ['make', '--help'], defaultproject=True)
		runPySys(self, 'clean', ['clean', '--help'], defaultproject=True)
			
	def validate(self):
		for t in ['noargs', 'toplevel', 'run', 'print', 'make', 'clean']:
			self.assertGrep(t+'.err', expr='.', contains=False)
			self.assertGrep(t+'.out', expr='Exception', contains=False)
			self.assertGrep(t+'.out', expr='.') # check not empty
			self.assertGrep(t+'.out', expr='.'*(120+1), contains=False) # check no lines are too long
			self.assertGrep(t+'.out', expr='WARNING', contains=False) # make sure no warnings about missing project files
			self.assertGrep(t+'.err', expr='WARNING', contains=False) # make sure no warnings about missing project files