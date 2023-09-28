__pysys_title__   = r""" Writers - JUnitXMLResultsWriter configuration """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-09-28"
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
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--record'], workingDir=self.input)
		
	def validate(self):
		self.assertThatGrep('junit-recommended/TEST-pkg1.pkg2.TestWithPackage.xml', 'testsuite.* name="([^"]*)"', expected='pkg1.pkg2')
		self.assertThatGrep('junit-recommended/TEST-pkg1.pkg2.TestWithPackage.xml', 'testcase.* name="([^"]*)"', expected='TestWithPackage')
		self.assertThatGrep('junit-recommended/TEST-pkg1.pkg2.TestWithPackage.xml', 'testcase.* classname="([^"]*)"', expected='')
		self.assertThatGrep('junit-recommended/TEST-TestWithMode~MyMode.xml', 'testsuite.* name="([^"]*)"', expected='')
		self.assertThatGrep('junit-recommended/TEST-TestWithMode~MyMode.xml', 'testcase.* name="([^"]*)"', expected='TestWithMode~MyMode')
		self.assertThatGrep('junit-recommended/TEST-TestWithMode~MyMode.xml', 'testcase.* classname="([^"]*)"', expected='')

		self.assertThatGrep('junit-default/TEST-pkg1.pkg2.TestWithPackage.xml', 'testsuite.* name="([^"]*)"', expected='pkg1.pkg2.TestWithPackage')
		self.assertThatGrep('junit-default/TEST-pkg1.pkg2.TestWithPackage.xml', 'testcase.* name="([^"]*)"', expected='pkg1.pkg2.TestWithPackage')
		self.assertThatGrep('junit-default/TEST-pkg1.pkg2.TestWithPackage.xml', 'testcase.* classname="([^"]*)"', expected='PySysTest')
		self.assertThatGrep('junit-default/TEST-TestWithMode~MyMode.xml', 'testsuite.* name="([^"]*)"', expected='TestWithMode~MyMode')
		self.assertThatGrep('junit-default/TEST-TestWithMode~MyMode.xml', 'testcase.* name="([^"]*)"', expected='TestWithMode~MyMode')
		self.assertThatGrep('junit-default/TEST-TestWithMode~MyMode.xml', 'testcase.* classname="([^"]*)"', expected='PySysTest')

		self.assertThatGrep('junit-special/TEST-pkg1.pkg2.TestWithPackage.xml', 'testcase.* classname="([^"]*)"', expected='class=PySysTest')
