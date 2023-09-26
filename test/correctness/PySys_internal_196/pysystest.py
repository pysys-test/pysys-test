__pysys_title__   = r""" BaseRunner/ProcessUser - handleRunnerAbort for Ctrl+C or signal interrupt handleRunnerAbort with sockets """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-11-25"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_groups__           = "myGroup, disableCoverage, performance"

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
		self.waitForGrep('myoutdir/Test_SocketWaitSeparateProcess/serversock.out', 'Server got client connection, now blocking forever', process=pysys)

		pysys.signal(signal.SIGINT)

		try:
			self.waitProcess(pysys, timeout=60)
		finally:
			self.logFileContents('pysys-run.out', maxLines=0)
			self.logFileContents('pysys-run.err', maxLines=0)
		
	def validate(self):
		self.assertGrep('pysys-run.out', 'WARN +PySys terminated early due to runner abort')
		self.assertGrep('myoutdir/Test_SocketWaitSeparateProcess/run.log', 'Test outcome reason: .*Test interrupted by runner abort')
		self.assertGrep('myoutdir/Test_SocketWaitSeparateProcess/run.log', 'Test final outcome: .*BLOCKED')
		self.assertGrep('pysys-run.out', 'Logging from customn handleRunnerAbort goes here')
