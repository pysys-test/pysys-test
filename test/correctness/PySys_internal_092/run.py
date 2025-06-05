import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def startPython(self, arguments, state=FOREGROUND, **kwargs):
		env = dict(os.environ)
		return self.startProcess(command=sys.executable, arguments=arguments, 
			environs=env, state=state, **kwargs)

	def execute(self):
		self.startPython(['-m', 'pysys', 'run', '-h', 'vDEBUG'], 
			stdout='pysys-print.out', stderr='pysys-print.err')
		self.logFileContents('pysys-print.out', maxLines=0)
		self.logFileContents('pysys-print.err', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys-print.out', expr='Usage: pysys.py print')