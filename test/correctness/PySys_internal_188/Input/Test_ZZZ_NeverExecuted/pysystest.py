__pysys_title__   = r""" Nested test should never get executed """ 
#                        ================================================================================

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.abort(FAILED, 'This test should never even start executing')
		
	def validate(self):
		pass
