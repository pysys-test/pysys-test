__pysys_title__   = r""" PerformanceReporter - Compare with baseline """ 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-02-04"

import pysys
from pysys.constants import *

import pysys.utils.logutils

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--cycle=3'], workingDir=self.input, 
			environs={'PYSYS_PERFORMANCE_BASELINES':'__pysys_performance/**/*.csv , __pysys_perform*/*/*.json '})
		
	def validate(self):
		#path = self.grep('pysys-run.out', 'Creating performance summary log file at: (.+)')
		self.logFileContents('pysys-run.out', maxLines=0, stripWhitespace=False)

		self.assertDiff(self.copy('pysys-run.out', 'perf-summary.out', mappers=[
			lambda line: pysys.utils.logutils.stripANSIEscapeCodes(line),
			pysys.mappers.IncludeLinesBetween('Performance comparison', stopBefore=' (CRIT|INFO) '),
			# strip out the bit that contains timestamps and hostnames from the current run
			pysys.mappers.RegexReplace('(  outDirName=myoutdir, ).*', r'\1<stripped>'),
		]))
		