__pysys_title__   = r""" BaseRunner/ProcessUser - early termination on interrupt """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-11-25"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
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

		pysys = self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--threads=2'], workingDir=self.input, state=BACKGROUND)
		self.waitForGrep('myoutdir/Test_ForegroundProcess/sleeper.out', 'Sleeping', process=pysys)
		self.waitForGrep('myoutdir/Test_Sleeps/run.log', 'Waiting for', process=pysys)

		pysys.signal(signal.SIGINT)
		#pysys.signal(signal.SIGINT)
		try:
			self.waitProcess(pysys, timeout=5) # TODO: increase timeout for real
		finally:
			self.logFileContents('pysys-run.out', maxLines=0)
			self.logFileContents('pysys-run.err', maxLines=0)
			self.logFileContents('myoutdir/Test_ForegroundProcess/sleeper.out', maxLines=0)
		
	def validate(self):
		self.assertGrep('pysys-run.out', 'Summary of failures:')
		self.assertGrep('pysys-run.out', 'WARN +PySys terminated early due to interruption')

		self.assertPathExists('myoutdir/Test_ZZZ_NeverExecuted', exists=False) # should not even start this one
		self.assertGrep('pysys-run.out', 'Test_ZZZ_NeverExecuted', contains=False)

		self.assertGrep('myoutdir/Test_Sleeps/run.log', 'Completed mycleanup function', assertMessage="Check that cleanup executes fully even after interruption")
		self.assertGrep('myoutdir/Test_Sleeps/cleanup_program.out', 'Cleanup completed by child process', assertMessage="Check that cleanup processes can execute even after interruption")
