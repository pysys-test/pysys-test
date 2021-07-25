import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re
from pysys.utils.filecopy import filecopy
from pysys.config.project import createProjectConfig

class PySysTest(BaseTest):

	def execute(self):
		createProjectConfig(self.output)
		self.pysys.pysys('make1', ['make', 'mynewtest1'])
		self.pysys.pysys('make2', ['make', 'mynewtest2'])
		
		self.copy('mynewtest1/pysystest.xml', 'mynewtest1/pysystest.xml', mappers=[
			pysys.mappers.RegexReplace(' TODO', '')
		])
		self.copy('mynewtest2/pysystest.xml', 'mynewtest2/pysystest.xml', mappers=[
			pysys.mappers.RegexReplace(' TODO', '')
		])
		
		self.pysys.pysys('run1', ['run', '-o', 'cleaned'])
		self.pysys.pysys('run2', ['run', '-o', 'notcleaned'])
		self.pysys.pysys('clean', ['clean', '-o', 'cleaned', '--all', 'mynewtest1'])
			
	def validate(self):
		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest1/Output/notcleaned/run.log'))
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/Output/cleaned/run.log'))

		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest2/Output/notcleaned/run.log'))
		self.assertThat('os.path.exists(%s)', repr(self.output+'/mynewtest2/Output/cleaned/run.log'))

		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/run.pyc')) # python2
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/mynewtest1/__pycache__')) # python3
