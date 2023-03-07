__pysys_title__   = r""" Samples - pysystestxml_upgrader.py """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-02-10"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		self.copy(self.project.testRootDir+'/../samples/cookbook/test/demo-tests/PySysTestXMLDescriptorSample', self.output+'/xmldemo/')
		self.copy(self.input+'/pysysproject.xml', self.output+'/xmldemo/')
		self.startPython([self.project.testRootDir+'/../samples/cookbook/util_scripts/pysystestxml_upgrader.py', 
			"del" if IS_WINDOWS else "rm", 
			"move" if IS_WINDOWS else "mv", 
			'.'], workingDir=self.output+'/xmldemo')
		self.pysys.pysys('pysys-print', ['print'], workingDir=self.output+'/xmldemo')
		
	def validate(self):
		self.logFileContents('xmldemo/pysys_upgrader.log', tail=True)
		self.assertDiff('xmldemo/PySysTestXMLDescriptorSample/pysystest.py', 'pysystest.py')