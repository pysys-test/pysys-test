import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

class PySysTest(BaseTest):

	def execute(self):
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read()) # define runPySys
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
