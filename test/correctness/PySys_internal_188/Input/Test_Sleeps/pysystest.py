__pysys_title__   = r""" Nested test that does a long wait """ 
#                        ================================================================================

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		def mycleanup(owner):
			owner.log.info('Called mycleanup function')
			owner.mkdir(owner.output)
			owner.startPython([self.input+'/cleanup_program.py'], stdouterr='cleanup_program')
			owner.log.info('Completed mycleanup function')

		self.addCleanupFunction(lambda: mycleanup(self))

		self.runner.addCleanupFunction(lambda: [mycleanup(self.runner), self.log.info('Called custom runner cleanup function')] )

		self.wait(120)
		
	def validate(self):
		pass
