__pysys_title__   = r""" Nested test that does a long wait """ 
#                        ================================================================================

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		def mycleanup():
			self.log.info('Called mycleanup function')
			self.startPython([self.input+'/cleanup_program.py'], stdouterr='cleanup_program')
			self.log.info('Completed mycleanup function')

		self.addCleanupFunction(mycleanup)
		self.wait(120)
		
	def validate(self):
		pass
