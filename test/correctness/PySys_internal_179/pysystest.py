__pysys_title__   = r""" PerformanceReporter - JSON""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-02-04"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance; inherit=true"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys
from pysys.constants import *
import json

from pysys.utils.perfreporter import CSVPerformanceFile

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '--cycle=3'], workingDir=self.input, expectedExitStatus='==2')
		self.logFileContents('pysys-run.out', tail=True)
		
	def validate(self):
		path = self.grep('pysys-run.out', 'Creating performance summary log file at: (.+json)')
		self.logFileContents(path)
		with open(path, encoding='utf-8') as f:
			data = json.load(f)
			self.assertThat('keys == expected', keys=sorted(list(data.keys())), expected=sorted(['runDetails', 'results']))
			self.assertThat('runDetails and results', runDetails=data['runDetails'], results=data['results'])
			self.assertThat('resultDetails == expected', resultDetails=data['results'][0]['resultDetails'], expected={
				'mode': 'MyMode', 'ModeParamA': 123, 'ModeParamB': 'Foo'
			})