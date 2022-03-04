__pysys_title__   = r""" Test Loading - microbenchmark of in-memory parsing different pysystest.* files""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-28"

__pysys_groups__           = "testLoading, performance, disableCoverage; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"
__pysys_modes__            = """ 
	lambda helper: helper.createModeCombinations(helper.inheritedModes, 
			[{'descriptorFile':v} for v in [
				'PythonLarge', 
				'PythonLargeNonString', 
				'PythonSmall', 
				'XmlLarge', 
				'XmlSmall', 
				# 'CreateEmptyDescriptor',
			]],
			)
	"""

import os, sys, math, shutil, glob

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	testDurationSecs = '4.0'

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		try:
			self.pysys.pysys('pysys', [
					'run', 
					'-XtestDurationSecs=%s'%self.testDurationSecs, 
					'-XdescriptorFile='+self.mode.params['descriptorFile']
				], defaultproject=True, workingDir='test')
		finally:
			self.logFileContents('pysys.err')

	def validate(self):
		self.addOutcome(PASSED, '')
		resultDetails = {'PythonVersion':'%s.%s'%sys.version_info[0:2], 'PySysVersion':pysys.__version__, 'DurationSecs':self.testDurationSecs}
		resultDetails.update(self.mode.params)
		
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'descriptor load rate is: ([^ ]+)'), 
			'DescriptorLoader in-memory parse rate for %s'%self.mode, 
			unit='/s', 
			resultDetails=resultDetails
			)
