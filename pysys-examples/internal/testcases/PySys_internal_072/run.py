import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		runPySys(self, 'toplevel', ['--help'])
		runPySys(self, 'run', ['run', '--help'])
		runPySys(self, 'print', ['print', '-h'])
		runPySys(self, 'make', ['make', '--help'])
			
	def validate(self):
		for t in ['toplevel', 'run', 'print', 'make']:
			self.assertGrep(t+'.err', expr='.', contains=False)
			self.assertGrep(t+'.out', expr='Exception', contains=False)
			self.assertGrep(t+'.out', expr='.') # check not empty
			self.assertGrep(t+'.out', expr='.'*(120+1), contains=False) # check no lines are too long
