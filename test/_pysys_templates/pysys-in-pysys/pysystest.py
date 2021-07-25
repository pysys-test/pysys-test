"""
<?xml version="1.0" standalone="yes"?>
<pysystest>

	<description> 
		<title>My category - My test title TODO</title>    
	</description>

<groups groups=""/>
</pysystest>
"""

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):

		#self.copy(self.input, self.output+'/test')
		self.pysys.pysys('pysys-run', ['run', '-o', 'myoutdir'], workingDir=self.input)
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		pass