__pysys_title__   = r""" Test Loading - measure real-world parsing of descriptors by DescriptorLoader""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-27"

__pysys_groups__           = "testLoading, performance, disableCoverage; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"
__pysys_modes__            = """ 
	lambda helper: helper.createModeCombinations(helper.inheritedModes, 
			[{'descriptorFile':v} for v in ['PythonLarge', 'PythonSmall', 'XmlLarge', 'XmlSmall']],
			#[{'chunksize':v} for v in [1, 2, 6, 8, 12, 16, 32, 64]],
			#[{'processWorkers':v} for v in [2, 4, 8, 16, 32, 48, 60]],
			)
	
	"""

import os, sys, math, shutil, glob

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	testDurationSecs = '4.0'
	testsPerLoader = 200

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		try:
			self.pysys.pysys('pysys', 
				[
					'run', 
					'-XtestDurationSecs=%s'%self.testDurationSecs, 
					'-XtestsPerLoader=%s'%self.testsPerLoader, 
					'-XdescriptorFile='+self.mode.params['descriptorFile']
				], defaultproject=True, workingDir='test', 
				environs={
					#'PYSYS_PROCESS_CHUNKSIZE': str(self.mode.params['chunksize']),
					#'PYSYS_PROCESS_WORKERS': str(self.mode.params['processWorkers']),
					})
		finally:
			self.logFileContents('pysys.err')

	def validate(self):
		self.addOutcome(PASSED, '')
		resultDetails = {'PythonVersion':'%s.%s'%sys.version_info[0:2], 'PySysVersion':pysys.__version__, 'DurationSecs':self.testDurationSecs}
		resultDetails.update(self.mode.params)
		resultDetails['testsPerLoader'] = self.testsPerLoader
		
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'descriptor load rate is: ([^ ]+)'), 
			'DescriptorLoader parse rate for %s'%self.mode, 
			unit='/s', 
			resultDetails=resultDetails
			)
