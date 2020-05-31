import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys-nomodes', ['run', '-o', 'pysys-nomodes'], workingDir='test')
		runPySys(self, 'pysys-withmodes', ['run', '-o', 'pysys-withmodes', '-m', 'mode1'], workingDir='test')
		runPySys(self, 'pysys-withemptymode', ['run', '-o', 'pysys-withemptymode', '-m', ''], workingDir='test')
		runPySys(self, 'pysys-unknownmodes', ['run', '-o', 'pysys-unknownmodes', '-m', 'mode-unknown'], workingDir='test')

		runPySys(self, 'pysys-multiplemodes-error', ['run', '-o', 'pysys-multiplemodes-error', '-m', 'mode1,mode2'], workingDir='test', expectedExitStatus=10)
		runPySys(self, 'pysys-modeexcludes-error', ['run', '-o', 'pysys-modeexcludes-error', '-m', '!mode1'], workingDir='test', expectedExitStatus=10)

		runPySys(self, 'pysys-withmodes-print', ['print', '-m', 'mode1'], workingDir='test')
		runPySys(self, 'pysys-unknownmodes-print', ['print', '-m', 'mode-unknown'], workingDir='test')
			
	def validate(self):
		self.assertGrep('pysys-nomodes.out', expr='Running test Test_WithModes with mode "None"')
		self.assertGrep('pysys-nomodes.out', expr='Running test Test_WithNoModes with mode "None"')

		self.assertGrep('pysys-withmodes.out', expr='Running test Test_WithModes with mode "mode1"')
		self.assertGrep('pysys-withmodes.out', expr='Test final outcome: *PASSED')
		self.assertGrep('pysys-withmodes.out', expr='Test outcome reason: *Unable to run test in mode1 mode') # for nomodes test
		self.assertGrep('pysys-withmodes.out', expr='Test final outcome: *SKIPPED') # for nomodes test

		self.assertGrep('pysys-withemptymode.out', expr='Running test Test_WithModes with mode ""')
		self.assertGrep('pysys-withemptymode.out', expr='Running test Test_WithNoModes with mode ""')
		self.assertGrep('pysys-withemptymode.out', expr='SKIPPED', contains=False)

		self.assertLineCount('pysys-unknownmodes.out', expr='Test final outcome: *SKIPPED', condition='==2')
		self.assertGrep('pysys-unknownmodes.out', expr='Running test .* with mode', contains=False)
		
		self.assertGrep('pysys-multiplemodes-error.err', expr='Cannot specify multiple modes unless supportMultipleModesPerRun=True')
		self.assertGrep('pysys-modeexcludes-error.err', expr='Cannot specify mode exclusions unless supportMultipleModesPerRun=True')

		self.assertGrep('pysys-unknownmodes-print.out', expr='.+', contains=False)
		self.assertGrep('pysys-withmodes-print.out', expr='Test_WithModes')
