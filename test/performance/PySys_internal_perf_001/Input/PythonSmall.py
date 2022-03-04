__pysys_title__   = r""" My testcase @TEST_ID@""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-27"

#__pysys_groups__           = "group1, group2"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"
#__pysys_modes__            = """ lambda helper: helper.createModeCombinations(helper.inheritedModes, helper.makeAllPrimary({'MyMode':{'MyParam':123}})) """

import os, sys, math, shutil, glob

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')

	def validate(self):
		self.addOutcome(PASSED, '')
