import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, 'pysys', ['run', '-o', self.output+'/test'], workingDir=self.input)
		runPySys(self, 'pysys-print', ['print', '-s', 'eXecutionOrderHint'], workingDir=self.input)
			
	def validate(self):
		self.assertOrderedGrep('pysys.out', exprList=['Id *: *Test%d'%x for x in [
			2, 3, 1, 4, 6, 5]]) 
		self.assertOrderedGrep('pysys-print.out', exprList=['Test%d'%x for x in [
			2, 3, 1, 4, 6, 5]]) 