import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys

class PySysTest(BaseTest):

	def execute(self):
		self.pythonDocTest(os.path.dirname(pysys.__file__)+'/utils/stringutils.py', 
			pythonPath=sys.path)
			
	def validate(self):
		return
		# ensure these appear at start of the line, which for some CI writers is important
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		