import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, 'pysys', ['run', '-o', self.output+'/testoutput'], workingDir=self.input)

	def validate(self):
		self.logFileContents('testoutput/NestedPass/run.log', includes=['.*[Ww]ait.*', '.*found.*'])

		self.assertGrep('testoutput/NestedPass/run.log', expr='Waiting for .*in myprocess.log')
		# by using a raw string and triple quotes and literal=True we can avoid the need to add any (additional) escaping for this assertion, 
		# so this is what's actually in the run.log
		self.assertGrep('testoutput/NestedPass/run.log', expr=
			r"""Waiting for '["\']Hello["\'] ' in myprocess.log (to ensure myprocess logs appropriate greetings); timeout=123.5s""", literal=True)
