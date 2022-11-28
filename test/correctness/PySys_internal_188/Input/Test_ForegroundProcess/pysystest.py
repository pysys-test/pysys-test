__pysys_title__   = r""" Nested test that runs a foreground process doing a long sleep """ 
#                        ================================================================================

import os, sys, math

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.startPython([self.input+'/sleeper.py'], stdouterr='sleeper')
		
	def validate(self):
		pass
