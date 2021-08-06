__pysys_title__   = r""" pysys.py make - pre-2.0 class""" 
#                        ================================================================================

__pysys_purpose__ = r""" The purpose of this test is to check that older projects that subclassed the old maker still 
	work.  """
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-08-06"

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		#self.copy(self.input, self.output+'/test')
		self.pysys.pysys('pysys-make-help', ['make', '--help'], workingDir=self.input)
		self.pysys.pysys('pysys-make', ['make', self.output+'/MyNewTest'], workingDir=self.input)
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		self.assertThat('paths == expected', paths=', '.join(pysys.utils.fileutils.listDirContents(self.output+'/MyNewTest')), 
			expected='pysystest.xml, run.py, Input/, Output/, Reference/')
		self.assertGrep('MyNewTest/pysystest.xml', 'myGroup')
		self.assertGrep('pysys-make-help.out', 'Customized (legacy) test maker MyLegacyMaker', literal=True)