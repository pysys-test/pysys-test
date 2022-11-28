__pysys_title__   = r""" ProcessUser and BaseRunner - early termination on interrupt """ 
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

		pysys = self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '-n2'], workingDir=self.input, state=BACKGROUND)
		self.waitForGrep('myoutdir/Test_ForegroundProcess/sleeper.out', 'Sleeping', process=pysys)
		self.waitForGrep('myoutdir/Test_Sleeps/run.log', 'Waiting for', process=pysys)

		#pysys.signal(signal.CTRL_C_EVENT if IS_WINDOWS else signal.SIGINT)

		pysys.signal(signal.SIGINT)
		self.waitProcess(pysys, timeout=5) # TODO: increase timeout for real

		self.logFileContents('pysys-run.out')
		
	def validate(self):
		pass