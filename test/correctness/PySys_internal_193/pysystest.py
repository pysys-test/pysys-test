__pysys_title__   = r""" Test loading - Non Python pysystest.XXX files and __pysys_user_data__ expansion""" 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-03-16"
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
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir'], workingDir=self.input)
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		self.assertThatGrep('pysys-run.out', 'Id: *(.*)', expected='MyNestedTestcase')
		self.assertThatGrep('pysys-run.out', 'Title: *(.*)', expected='This is a non-Python PySys test')
		self.assertThatGrep('pysys-run.out', 'Test userdata1: *(.*)', expected="'resolved_project_prop,second_thing value'")
		self.assertThatGrep('pysys-run.out', 'Test userdata2: *(.*)', expected="['a', 'resolved_project_prop', 'second_thing', '${escaped} b']") # expansion of props (except when escaped), type coersion to list
		self.assertThatGrep('pysys-run.out', 'Test userdataInt: *(.*)', expected="12345")
		self.assertGrep('pysys-run.out', 'This is a custom test ')
