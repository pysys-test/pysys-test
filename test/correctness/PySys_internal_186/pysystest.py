__pysys_title__   = r""" ThreadPoolExecutor""" 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-11-21"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *



class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '-vDEBUG'], workingDir=self.input)
		self.logFileContents('pysys-run.out', tail=True, maxLines=40)
		
	def validate(self):
		self.assertThatGrep('myoutdir/MyNestedTestcase/run.log', 'Initialized PySys background thread: (.*)', 'value.startswith(expected)',  expected='MyNestedTestcase:ThreadPoolExecutor')
		self.assertGrep('myoutdir/MyNestedTestcase/run.log', 'INFO.*Log message from submitted thread job')
		self.assertGrep('myoutdir/MyNestedTestcase/run.log', 'Background thread has completed waiting')
		self.assertGrep('myoutdir/MyNestedTestcase/run.log', 'Completed shutdown of thread pool')
