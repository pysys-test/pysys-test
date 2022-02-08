__pysys_title__   = r""" Nested """ 
#                        ================================================================================

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.reportPerformanceResult(1000+(self.testCycle+1)*10, 'Rate of doing a foo bar', '/s')
		self.reportPerformanceResult(2000+(self.testCycle+1), 'Rate of doing a badda-badda-bing', '/s')
		
	def validate(self):
		self.addOutcome(PASSED)
