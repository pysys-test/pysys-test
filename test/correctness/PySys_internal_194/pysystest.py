__pysys_title__   = r""" Project loading - PYSYS_PROJECT_APPEND """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-07-21"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):

		self.pysys.pysys('pysys-debug', ['debug'], workingDir=self.input, environs={'PYSYS_PROJECT_APPEND':
			self.input+'/pysysproject-extra.xml'+','+self.input+'/pysysproject-extra2.xml'})
		self.pysys.pysys('pysys-run', ['run'], workingDir=self.input, environs={'PYSYS_PROJECT_APPEND':
			self.input+'/pysysproject-extra.xml'+','+self.input+'/pysysproject-extra2.xml'})
		self.logFileContents('pysys-debug.out')
		
	def validate(self):
		self.assertGrep('pysys-debug.out', 'mainProperty = mymainvalue')
		self.assertGrep('pysys-debug.out', 'extraProperty = mymainvalue and mymainvalue')
		self.assertGrep('pysys-debug.out', 'extraProperty2 = mymainvalue and mymainvalue')

		# extra writer was enabled by the appended project xml
		self.assertGrep('pysys-run.out', 'CustomWriter.processResult: PySys_NestedTestcase')
