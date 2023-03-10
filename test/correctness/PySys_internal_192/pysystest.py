__pysys_title__   = r""" pysys.py - set-default-maker-template """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2023-03-10"
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
		self.pysys.pysys('pysys-make-list-root', ['make', '-h'], workingDir=self.input)
		self.pysys.pysys('pysys-make-list-dir1', ['make', '-h'], workingDir=self.input+'/dir1')
		self.pysys.pysys('pysys-make-list-dir2', ['make', '-h'], workingDir=self.input+'/dir1/dir2')

	def validate(self):
		self.logFileContents('pysys-make-list-dir2.out', maxLines=0)
		self.assertThatGrep('pysys-make-list-root.out', '^ +([^ ]+) *-', expected='tmpl2', mappers=[pysys.mappers.IncludeLinesBetween('Available templates')])
		self.assertThatGrep('pysys-make-list-dir1.out', '^ +([^ ]+) *-', expected='tmpl3', mappers=[pysys.mappers.IncludeLinesBetween('Available templates')])
		self.assertThatGrep('pysys-make-list-dir2.out', '^ +([^ ]+) *-', expected='tmpl4', mappers=[pysys.mappers.IncludeLinesBetween('Available templates')])
