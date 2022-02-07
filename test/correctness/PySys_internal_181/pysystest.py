__pysys_title__   = r""" PerformanceReporter - Compare with baseline, from test and standalone """ 
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

		self.startPython([os.path.dirname(pysys.__file__)+'/perf/perfreportstool.py', 
			'compare', 
			# all of 3 of these have some outdir so will generate a label based on something else
			'__pysys_performance/**/*.csv', 
			'__pysys_perform*/*/*.json',
			'perf_run3.json',
			], workingDir=self.input, stdouterr='perf-compare')
		
	def validate(self):
		self.logFileContents('pysys-run.out', maxLines=0, stripWhitespace=False, tail=True, color=False)

		self.logFileContents('perf-compare.out', maxLines=0, stripWhitespace=False, tail=True, color=False)
		
		self.assertDiff(self.copy('pysys-run.out', 'perf-summary.out', mappers=[
			lambda line: pysys.utils.logutils.stripANSIEscapeCodes(line),
			pysys.mappers.IncludeLinesBetween('Performance comparison', stopBefore=' (CRIT|INFO) '),
			# strip out the bit that contains timestamps and hostnames from the current run; all kinds of details like OS and cpu count could also differ
			pysys.mappers.RegexReplace('(  outDirName=[^,]*, ).*', r'\1<stripped>'),
			#pysys.mappers.RegexReplace(r'( from ).*(perf_.*)', r'\1<stripped>\2'),
		]))

		self.assertDiff(self.copy('perf-compare.out', 'perf-compare-no-colors.out', mappers=[
			lambda line: pysys.utils.logutils.stripANSIEscapeCodes(line),
			lambda line: line.replace('\\', '/') if ' from ' in line else line, # windows path separator used in "from ..." filename
			
		]))
