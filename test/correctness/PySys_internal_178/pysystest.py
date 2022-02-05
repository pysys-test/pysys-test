__pysys_title__   = r""" PerformanceReporter - default configuration, multi-cycle aggregation, summary""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-02-04"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"
#__pysys_modes__            = """ lambda helper: helper.combineModeDimensions(helper.inheritedModes, helper.makeAllPrimary({'MyMode':{'MyParam':123}})) """

import pysys
from pysys.constants import *

from pysys.utils.perfreporter import CSVPerformanceFile

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--cycle=3'], workingDir=self.input)
		self.logFileContents('pysys-run.out', tail=True)
		
	def validate(self):
		path = self.grep('pysys-run.out', 'Creating performance summary log file at: (.+)')
		f = CSVPerformanceFile.load(path)
		self.assertThat('len(runDetails) > 0', runDetails=f.runDetails) # not empty
		self.assertThat('resultsLen == expected', resultsLen=len(f.results), expected=2)
		self.assertThat('result1samples == expected', result1samples=f.results[0]['samples'], expected=3)
		self.assertThat('result2stdDev == expected', result2stdDev=f.results[-1]['stdDev'], expected=10.0)

		self.assertDiff(self.copy('pysys-run.out', 'perf-summary.out', mappers=[
			pysys.mappers.RegexReplace(pysys.mappers.RegexReplace.DATETIME_REGEX+' ', ''),
			pysys.mappers.IncludeLinesBetween(startAfter='Summary of performance results ', stopBefore='^INFO *$'),
		]))
