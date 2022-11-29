@@DEFAULT_DESCRIPTOR@@

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):

		#self.copy(self.input, self.output+'/test')
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir'], workingDir=self.input)
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		pass