import os, sys, re, shutil
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
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
