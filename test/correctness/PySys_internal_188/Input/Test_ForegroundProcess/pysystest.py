__pysys_title__   = r""" Nested test that runs a foreground process doing a long sleep """ 
#                        ================================================================================

import os, sys, math

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

		self.startPython([self.input+'/sleeper.py'], stdouterr='sleeper')
		
	def validate(self):
		pass
