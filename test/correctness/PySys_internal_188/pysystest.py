__pysys_title__   = r""" BaseRunner/ProcessUser - early termination on interrupt """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-11-25"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_groups__           = "myGroup, disableCoverage, performance"
__pysys_modes__            = lambda helper: [ 
	{'mode':'SIGINT_MT', 'interruptSignal':'SIGINT', 'multithreaded':True}, # primary mode
	{'mode':'SIGINT_ST', 'interruptSignal':'SIGINT', 'multithreaded':False}, 
	{'mode':'SIGTERM_MT', 'interruptSignal':'SIGTERM', 'multithreaded':True}, 
]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import os, sys, math, shutil, glob, signal

import pysys.basetest, pysys.mappers
from pysys.constants import *
from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):
		# Tried to test this on Windows but sending Ctrl+C to child also kills parent PySys instance, and 
		# dwCreationFlags|=win32process.CREATE_NEW_CONSOLE doesn't solve it (AND creates new interactive cmd windows)
		if IS_WINDOWS: self.skipTest("Cannot test signal interruption on Windows")

		pysys = self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--threads=2' if self.mode.params['multithreaded'] else '--threads=1', '-vdebug', '-XcodeCoverage'], workingDir=self.input, state=BACKGROUND)
		self.waitForGrep('pysys-run.out', 'Starting test execution', process=pysys) # MUST wait till we've completed the startup phase before interrupting else we can mess up the coverage initialization
		self.waitForGrep('myoutdir/Test_ForegroundProcess/sleeper.out', 'Sleeping', process=pysys)

		if self.mode.params['multithreaded']:
			self.waitForGrep('myoutdir/Test_Sleeps/run.log', 'Waiting for', process=pysys)

		if self.mode.params['interruptSignal'] == 'SIGINT':
			pysys.signal(signal.SIGINT)
		else:
			pysys.signal(signal.SIGTERM)

		try:
			self.waitProcess(pysys, timeout=60)
		finally:
			self.logFileContents('pysys-run.out', maxLines=0)
			self.logFileContents('pysys-run.err', maxLines=0)
		
	def validate(self):
		self.assertGrep('pysys-run.out', 'WARN +PySys terminated early due to interruption')

		self.assertGrep('pysys-run.out', 'Summary of failures:', assertMessage='Assert we still display a summary of failures from writers despite interruption')

		# Check we report results for both tests
		self.assertGrep('pysys-run.out', 'BLOCKED: Test_ForegroundProcess')
		if self.mode.params['multithreaded']:
			self.assertGrep('pysys-run.out', 'BLOCKED: Test_Sleeps')
			self.assertGrep('pysys-run.out', 'TERMINATED EARLY; 1 TESTS DID NOT START')

		self.assertPathExists('myoutdir/Test_ZZZ_NeverExecuted', exists=False) # should not even start this one
		self.assertGrep('pysys-run.out', 'Test_ZZZ_NeverExecuted', contains=False)

		self.assertGrep('pysys-run.out', 'Called custom runner cleanup function')

		self.assertGrep('pysys-run.out', 'WARN  Writer PythonCoverageWriter failed during cleanup due to interruption') # don't want to waste time running code coverage tools during cleanup

		self.assertGrep('myoutdir/Test_ForegroundProcess/run.log', 'Completed mycleanup function', assertMessage="Check that TEST cleanup executes fully even after interruption")
		self.assertGrep('myoutdir/Test_ForegroundProcess/cleanup_program.out', 'Cleanup completed by child process', assertMessage="Check that TEST cleanup processes can execute even after interruption")
		self.assertGrep('myoutdir/__pysys_runner.myoutdir/cleanup_program.out', 'Cleanup completed by child process', assertMessage="Check that RUNNER cleanup processes can execute even after interruption")
