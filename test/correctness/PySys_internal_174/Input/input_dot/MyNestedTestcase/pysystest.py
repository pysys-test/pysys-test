__pysys_title__   = r""" Nested test """ 

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.log.info('Input dir = %s', self.input)
		self.assertPathExists(self.input+'/inputfile.txt')
		self.copy(self.input, self.output)
		
	def validate(self):
		pass
