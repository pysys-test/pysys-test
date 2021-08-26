__pysys_title__   = r""" pysys.py - debug """ 
#                        ================================================================================

__pysys_purpose__ = r""" The purpose of this test is to touch-test the "pysys debug" command. 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-08-22"

#__pysys_groups__           = "myGroup, disableCoverage, performance; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		self.pysys.pysys('pysys-debug', ['debug'], workingDir=self.project.testRootDir)
		self.logFileContents('pysys-debug.out')
		
	def validate(self):
		self.assertGrep('pysys-debug.out', 'Using PySys .* from .*')