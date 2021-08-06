import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re
from pysys.utils.filecopy import filecopy
from pysys.config.project import createProjectConfig

class PySysTest(BaseTest):

	def execute(self):
		createProjectConfig(self.output)
		self.pysys.pysys('make1', ['make', 'MyNewTest1'])
		self.pysys.pysys('make2', ['make', 'MyNewTest2'])
		
		self.copy('MyNewTest1/pysystest.py', 'MyNewTest1/pysystest.py', mappers=[
			pysys.mappers.RegexReplace(' TODO', '')
		])
		self.copy('MyNewTest2/pysystest.py', 'MyNewTest2/pysystest.py', mappers=[
			pysys.mappers.RegexReplace(' TODO', '')
		])
		
		self.pysys.pysys('run1', ['run', '-o', 'cleaned'])
		self.pysys.pysys('run2', ['run', '-o', 'notcleaned'])
		self.pysys.pysys('clean', ['clean', '-o', 'cleaned', '--all', 'MyNewTest1'])
			
	def validate(self):
		self.assertThat('os.path.exists(%s)', repr(self.output+'/MyNewTest1/Output/notcleaned/run.log'))
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/MyNewTest1/Output/cleaned/run.log'))

		self.assertThat('os.path.exists(%s)', repr(self.output+'/MyNewTest2/Output/notcleaned/run.log'))
		self.assertThat('os.path.exists(%s)', repr(self.output+'/MyNewTest2/Output/cleaned/run.log'))

		self.assertThat('not os.path.exists(%s)', repr(self.output+'/MyNewTest1/run.pyc')) # python2
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/MyNewTest1/__pycache__')) # python3
