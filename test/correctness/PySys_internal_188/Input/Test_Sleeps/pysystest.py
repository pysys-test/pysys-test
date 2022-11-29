__pysys_title__   = r""" Nested test that does a long wait """ 
#                        ================================================================================

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		self.wait(120)
		
	def validate(self):
		pass
