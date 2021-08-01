__pysys_title__   = r""" Test Loading - various self.input dirs """ 
#                        ========================================================================================================================

__pysys_purpose__ = r""" The purpose of this test is to check the autodetection setting for the test input dir 
	(use Input/ if it exists else testDir), as well as the default project option of ".". 
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-08-01"

#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		self.copy(self.input, self.output+'/pysys-tests')
		self.pysys.pysys('pysys-run', ['run', '-vDEBUG'], workingDir='pysys-tests')
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		self.assertGrep('pysys-run.out', ' WARN .*Copy will ignore .*to avoid recursive copy')
