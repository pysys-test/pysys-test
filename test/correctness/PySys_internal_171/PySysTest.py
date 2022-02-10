__pysys_title__   = r""" Test loading - Descriptors in a pysystest.py file, multiple encodings, __pysys_ after import, regex+Python exec """ 
#                        ================================================================================

__pysys_purpose__ = r""" 
	This is a fairly thorough test of the (non-error) behaviour for both Python exec parsing and regex-based parsing (with DisablePythonParse). 
	
	It includes nested XML descriptors inside python headers, handling of multiple file encodings. 
	
	It also exercises the logic whereby the performance optimization is abandoned if a __pysys_ line if found after the first import. 
	""" 

__pysys_modes__ = lambda helper: helper.makeAllPrimary({
	'DisablePythonParse':{'disablePythonParse':True},
	'StandardPythonParse':{'disablePythonParse':False},
})

__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-01"

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/pysys-output'], workingDir=self.input, 
			environs={'PYSYS_DISABLE_PYTHON_DESCRIPTOR_PARSING':str(self.mode.params['disablePythonParse'])})
		self.pysys.pysys('pysys-print', ['print', '--json'], workingDir=self.input,
			environs={'PYSYS_DISABLE_PYTHON_DESCRIPTOR_PARSING':str(self.mode.params['disablePythonParse'])})

	def validate(self):
		self.logFileContents('pysys-run.out')
		self.logFileContents('pysys-print.out', maxLines=0)
	
		json = pysys.utils.fileutils.loadJSON(self.output+'/pysys-print.out')
		titles = [t['title'] for t in json]
		self.assertThat('titles == expected', titles=titles, expected=[
			"My latin-1 encoded descriptor '\u00a3'",
			"My UTF-8 encoded descriptor '\u00a3'",
			"My UTF-8 encoded descriptor '\u00a3' <>",
		])