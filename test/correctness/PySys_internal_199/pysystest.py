__pysys_title__   = r""" pysys.py - writer enablement with --writer """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-09-29"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):

		#self.copy(self.input, self.output+'/test')
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', 
			'--writer=JSONResultsWriter', # unqualified
			'--writer=pysys.writer.outcomes.TextResultsWriter', # qualified
			'--writer', 'XMLResultsWriter',
			# NOT CSVResultsWriter
		], workingDir=self.input)
		
	def validate(self):
		self.assertThat('writers == expected', writers=sorted(os.path.basename(p) for p in glob.glob(self.output+"/myoutdir/testsummary*")), expected=[
			'testsummary.json', 
			'testsummary.log', 
			'testsummary.xml'])
