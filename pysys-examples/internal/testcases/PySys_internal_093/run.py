import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, os.path.join(self.output,'test'))

		subtest = 'printLogs-all-ST'
		runPySys(self, subtest, ['run', '--printLogs', 'aLL', '--threads', '1', '-o', subtest], workingDir='test', ignoreExitStatus=True)

		subtest = 'printLogs-failures-ST'
		runPySys(self, subtest, ['run', '--printLogs', 'failureS', '--threads', '1', '-o', subtest], workingDir='test', ignoreExitStatus=True)

		subtest = 'printLogs-failures-MT'
		runPySys(self, subtest, ['run', '--printLogs', 'failureS', '--threads', '2', '-o', subtest], workingDir='test', ignoreExitStatus=True)
		
		subtest = 'printLogs-none-ST'
		runPySys(self, subtest, ['run', '--printLogs', 'noNe', '--threads', '1', '-o', subtest], workingDir='test', ignoreExitStatus=True)

		subtest = 'printLogs-none-MT'
		runPySys(self, subtest, ['run', '--printLogs', 'none', '--threads', '2', '-o', subtest], workingDir='test', ignoreExitStatus=True)

		subtest = 'printLogs-none-ST-warn'
		runPySys(self, subtest, ['run', '--printLogs', 'none', '--threads', '1', '--verbosity', 'WARN', '-o', subtest], workingDir='test', ignoreExitStatus=True)

		subtest = 'printLogs-failures-ST-warn'
		runPySys(self, subtest, ['run', '--printLogs', 'failureS', '--threads', '1', '--verbosity', 'WARN', '-o', subtest], workingDir='test', ignoreExitStatus=True)
			
	def validate(self):
	
		subtests = [
			'printLogs-all-ST',
			'printLogs-failures-ST',
			'printLogs-failures-MT',
			'printLogs-none-ST', 
			'printLogs-none-MT',
			'printLogs-none-ST-warn',
			'printLogs-failures-ST-warn',
		]
	
		for subtest in subtests:
			self.assertGrep('%s.out'%subtest, expr='Id *: *NestedFail', contains=
				'none' not in subtest and 'warn' not in subtest)
			self.assertGrep('%s.out'%subtest, expr='Id *: *NestedPass', contains=
				'all' in subtest)
		self.log.info('')
		
		# should still get summary at end in all cases
		for subtest in subtests:
			self.assertOrderedGrep('%s.out'%subtest, exprList=['Summary of failures:', 'NestedTimedout'])
		self.log.info('')

		# even at WARN level we normally all log outcomes, even though run.log printing is suppressed by the log level
		self.assertOrderedGrep('printLogs-failures-ST-warn.out', exprList=[
			'FAILED: *NestedFail',
			'PASSED: *NestedPass',
			'WARN.*Reason for timed out outcome is general tardiness',
			'Summary of failures:'
			])
		# except in NONE mode
		self.assertOrderedGrep('printLogs-none-ST-warn.out', exprList=[
			'FAILED: *NestedFail',
			'Summary of failures:'
			], contains=False)
