import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, io

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	RUN_SUBTESTS = [ # name, args, expectedoutput tests (comma-separated)
	
		# test the --mode/modeincludes options (including the ! syntax for excludes)
		('run-noargs', ['run'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('run-primary', ['run', '--mode', 'PRIMARY'], 'Test_WithModes~mode1,Test_WithNoModes'),
		('run-all', ['run', '--mode', 'ALL'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3,Test_WithNoModes'),
		('run-not-primary', ['run', '--mode', '!PRIMARY'], 'Test_WithModes~mode2,Test_WithModes~mode3'),
		('run-not-mode1', ['run', '--mode', '!mode1,!mode3'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('run-modes-1-3', ['run', '--modeinclude', 'mode1,mode3'], 'Test_WithModes~mode1,Test_WithModes~mode3'),
		('run-primary-and-mode', ['run', '--mode', 'PRIMARY,mode2'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithNoModes'),
		('run-positive-and-negative', ['run', '--mode', 'PRIMARY,mode2,!mode1'], 'Test_WithModes~mode2,Test_WithNoModes'),
		('run-no-modes', ['run', '--mode', ''], 'Test_WithNoModes'),
		('run-not-no-modes', ['run', '--mode', '!'], 'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# test --modeexcludes
		('run-positive-and-negative-modeexclude', ['run', '-m', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1'], 
			'Test_WithModes~mode2,Test_WithNoModes'),
		('run-not-no-modes-modeexclude', ['run', '--modeexclude', ''], 
			'Test_WithModes~mode1,Test_WithModes~mode2,Test_WithModes~mode3'),
		
		# testid~mode test specs
		('run-standard-spec', ['run', '--mode', 'PRIMARY', '--mode', 'mode2', '--modeexclude','mode1', 'Test_WithNoModes', 'Test_WithModes'], 
			'Test_WithModes~mode2,Test_WithNoModes'),

		('run-mode-spec', ['run', 'Test_WithModes~mode2', 'Test_WithModes~mode3'], 
			'Test_WithModes~mode2,Test_WithModes~mode3'),		
	]
	
	PRINT_SUBTESTS = [ # name, args, exectedoutput
		('print-test-with-modes', ['print', '-m', 'mode3'], 'Test_WithModes'),
		('print-test-with-modes-none', ['print', '--mode', ''], 'Test_WithModes,Test_WithNoModes'),
		('print-test-spec-with-modes', ['print', 'Test_WithModes~mode2', 'Test_WithModes~mode3'], 'Test_WithModes~mode2,Test_WithModes~mode3'),
	
	]

	def execute(self):
		self.copy(self.input, self.output+'/test')

		# output directory handling with modes
		runPySys(self, 'run-relative-outdir', 
			['run', '--outdir', 'outdir-relative', '--mode=ALL'], workingDir='test', background=True)

		runPySys(self, 'run-absolute-outdir', 
			['run', '--outdir', self.output+'/outdir-absolute', '--mode=ALL'], workingDir='test', background=True)

		runPySys(self, 'run-absolute-outdir-cycles', 
			['run', '--outdir', self.output+'/outdir-absolute-cycles', '-c', '2'], workingDir='test', background=True)
			
		# detailed testcase selection testing
		for subid, args, _ in reversed(self.RUN_SUBTESTS):
			runPySys(self, subid, [args[0]]+['--outdir', 'out-%s'%subid]+args[1:], workingDir='test', background=True)
	
		for subid, args, _ in reversed(self.PRINT_SUBTESTS):
			runPySys(self, subid, args, workingDir='test', background=True)
		
		self.waitForBackgroundProcesses()
	
		# failure cases
		runPySys(self, 'error-run-specific-test-with-mode-exclusion', 
			['run', '-m', '!mode1,!mode2,!mode3', 'Test_WithModes'], workingDir='test', expectedExitStatus=10)
		self.assertGrep('error-run-specific-test-with-mode-exclusion.err', 
			expr='Test "Test_WithModes" cannot be selected with the specified mode[(]s[)].')

		runPySys(self, 'error-run-mode-with-range', 
			['run', 'SomeId1:2~MyMode'], workingDir='test', expectedExitStatus=10)
		self.assertGrep('error-run-mode-with-range.err', 
			expr='A ~MODE test mode selector can only be use with a test id, not a range or regular expression')

		runPySys(self, 'error-run-nonexistent-mode', 
			['run', '--mode', 'MyNonExistentMode', 'MyTest'], workingDir='test', expectedExitStatus=10)
		self.assertGrep('error-run-nonexistent-mode.err', 
			expr='ERROR: Unknown mode "MyNonExistentMode": the available modes for descriptors in this directory are: mode1, mode2, mode3')

		runPySys(self, 'error-run-wrong-case', 
			['run', '--mode', 'mOde1', 'Test_WithModes'], workingDir='test', expectedExitStatus=10)
		self.assertGrep('error-run-wrong-case.err', 
			expr='ERROR: Unknown mode "mOde1": the available modes for descriptors in this directory are: mode1, mode2, mode3')

		runPySys(self, 'error-run-nonexistent-spec-mode', 
			['run', 'Test_WithModes~NonExistentMode', ], workingDir='test', expectedExitStatus=10)
		self.assertGrep('error-run-nonexistent-spec-mode.err', 
			expr='ERROR: Unknown mode "NonExistentMode": the available modes for this test are: mode1, mode2, mode3')
		
		
	def validate(self):
		for subid, args, expectedids in self.RUN_SUBTESTS:
			self.log.info('%s:', subid)
			actualids = self.getExprFromFile(subid+'.out', expr='Id *: *([^ \n]+)', returnAll=True)
			self.assertThat('%r == %r', expectedids, ','.join(actualids))
			self.assertLineCount(subid+'.out', expr='Test final outcome: *PASSED', condition='==%d'%len(actualids))
			self.log.info('')

		for subid, args, expectedids in self.PRINT_SUBTESTS:
			self.log.info('%s:', subid)
			actualids = self.getExprFromFile(subid+'.out', expr='(.[^| ]+) *|', returnAll=True)
			self.assertThat('%r == %r', expectedids, ','.join(actualids))
			self.log.info('')
			
		# test output dirs must be unique; mode gets added somewhere different for relative vs absolue outdirs
		self.assertPathExists('outdir-absolute/Test_WithNoModes/run.log')
		self.assertPathExists('outdir-absolute/Test_WithModes~mode1/run.log')
		self.assertPathExists('outdir-absolute/Test_WithModes~mode2/run.log')
		
		self.assertPathExists('test/Test_WithNoModes/Output/outdir-relative/run.log')
		self.assertPathExists('test/Test_WithModes/Output/outdir-relative~mode1/run.log')
		self.assertPathExists('test/Test_WithModes/Output/outdir-relative~mode2/run.log')

		self.assertPathExists('outdir-absolute-cycles/Test_WithModes~mode1/cycle2/run.log')
		