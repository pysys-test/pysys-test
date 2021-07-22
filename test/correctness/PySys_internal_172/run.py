import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.pysys.pysys('pysys-make-root', ['make', '-h'], workingDir=self.input)
		self.pysys.pysys('pysys-make-dir1', ['make', '-h'], workingDir=self.input+'/dir1')
		self.pysys.pysys('pysys-make-dir2', ['make', '-h'], workingDir=self.input+'/dir1/dir2')

	def validate(self):
		self.logFileContents('pysys-make-dir2.out', maxLines=0)
	
		for x in ['pysys-make-root', 'pysys-make-dir1', 'pysys-make-dir2']:
			self.logFileContents(self.copy(x+'.out', x+'.txt', mappers=[pysys.mappers.IncludeLinesBetween(startAfter='Available templates')]))
			self.assertDiff(x+'.txt')