__pysys_title__   = r""" pysys.py - print descriptor suffix with directory names """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-09-27"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):

		#self.copy(self.input, self.output+'/test')
		self.pysys.pysys('pysys-print', ['print', 
			'Test', # should catch Test but not Test1
			'subdir1/TestSub1A', # relative path us
			os.path.abspath(self.input+'/subdir1')+os.sep+'TestSUB1B', # absolute path, os separator, case insensitivity
			# but not TestSub1C
			'subdir2', # a dir with nested items
			], workingDir=self.input)
		self.logFileContents('pysys-print.out')
		
	def validate(self):
		self.assertDiff('pysys-print.out')