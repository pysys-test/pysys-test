__pysys_title__   = r""" pysys.py - run --sort=random """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-03-11"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '-c4', '--sort=random'], workingDir=self.input)
		self.logFileContents('pysys-run.out', includes=['Id: .*'])
		
	def validate(self):
		self.addOutcome(PASSED, 'Just checking it doesn\t crash')