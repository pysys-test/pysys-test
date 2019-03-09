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
		self.startPython(['-m', 'pysys', 'print', '-h'], 
			stdout='pysys-print.out', stderr='pysys-print.err')
			
	def validate(self):
		self.assertGrep('pysys-print.out', expr='Usage: pysys.py print')