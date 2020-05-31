import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, io

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):
	def execute(self):
		self.copy(self.input, self.output+'/test')

		runPySys(self, 'run-relative-outdir', 
			['run', '--outdir', 'outdir-relative', '--mode=ALL'], workingDir='test')
		runPySys(self, 'run-absolute-outdir', 
			['run', '--outdir', self.output+'/outdir-absolute', '--mode=ALL'], workingDir='test')

		runPySys(self, 'clean-relative-outdir', 
			['clean', '-v', 'DEBUG', '--all', '--outdir', 'outdir-relative', #'--mode=ALL'
			], workingDir='test')
		runPySys(self, 'clean-absolute-outdir', 
			['clean', '-vDEBUG', '--outdir', self.output+'/outdir-absolute', #'--mode=ALL'
			], workingDir='test')

	def validate(self):
		self.logFileContents('clean-relative-outdir.out')
		self.logFileContents('clean-absolute-outdir.out')
		self.assertPathExists('test/Test_WithModes/Output/outdir-relative~mode1/run.log', exists=False)
		self.assertPathExists('test/Test_WithModes/Output/outdir-relative~mode2', exists=False)
		self.assertPathExists('test/Test_WithModes/Output/outdir-relative~mode2', exists=False)
		self.assertPathExists('test/Test_WithModes/Output', exists=True)

		self.assertPathExists('outdir-absolute/Test_WithModes~mode1', exists=False)
		self.assertPathExists('outdir-absolute/Test_WithModes~mode2', exists=False)
		self.assertPathExists('outdir-absolute', exists=True) # shouldn't blow the whole thing away
