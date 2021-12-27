__pysys_title__   = r""" Test Loading - measure DescriptorLoader and parsing of pysystest.py files""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-27"

__pysys_groups__           = "testLoading, performance, disableCoverage; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"
#__pysys_modes__            = """ lambda helper: helper.combineModeDimensions(helper.inheritedModes, helper.makeAllPrimary({'MyMode':{'MyParam':123}})) """

import os, sys, math, shutil, glob

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	testDurationSecs = '4.0'

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		try:
			self.pysys.pysys('pysys', ['run', '-XtestDurationSecs=%s'%self.testDurationSecs], defaultproject=True, workingDir='test')
		finally:
			self.logFileContents('pysys.err')

	def validate(self):
		self.addOutcome(PASSED, '')
		resultDetails = {'PythonVersion':'%s.%s'%sys.version_info[0:2], 'PySysVersion':pysys.__version__, 'DurationSecs':self.testDurationSecs}
		
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'small descriptor load rate is: ([^ ]+)'), 
			'DescriptorLoader parse rate for Python small descriptors', 
			unit='/s', 
			resultDetails=resultDetails
			)
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'large descriptor load rate is: ([^ ]+)'), 
			'DescriptorLoader parse rate for Python large descriptors', 
			unit='/s', 
			resultDetails=resultDetails
			)
