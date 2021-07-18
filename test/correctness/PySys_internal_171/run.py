import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/pysys-output'], workingDir=self.input)
		self.pysys.pysys('pysys-print', ['print', '--json'], workingDir=self.input)

	def validate(self):
		self.logFileContents('pysys-run.out')
		self.logFileContents('pysys-print.out', maxLines=0)
	
		json = pysys.utils.fileutils.loadJSON(self.output+'/pysys-print.out')
		titles = [t['title'] for t in json]
		self.assertThat('titles == expected', titles=titles, expected=[
			"My latin-1 encoded descriptor '\u00a3'",
			"My UTF-8 encoded descriptor '\u00a3'",
		])