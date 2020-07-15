import os, sys
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		self.pythonDocTest(os.path.dirname(pysys.__file__)+'/mappers.py', 
			pythonPath=sys.path)
			
	def validate(self):
		pass # all validation is done by pythonDocTest