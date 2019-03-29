import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil
from pysys.utils.pycompat import PY2
from pysys.utils.fileutils import *
from pysys.xml.project import createProjectConfig

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, self.output+'/test')

		longoutputdir = self.output+'/'+('x'*(256-len(self.output)))+'/outdir'
		# since this path causes problems for many tools, delete it even if this tests isn't in purge mode
		self.addCleanupFunction(lambda: self.deletedir(os.path.dirname(longoutputdir)))
		
		try:
			runPySys(self, 'pysys', ['run', '-o', longoutputdir, '--purge'], defaultproject=True)
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err', maxLines=0)

		self.assertPathExists(longoutputdir+'/NestedTest/run.log') # sanity check for the below)
		self.assertPathExists(longoutputdir+'/NestedTest/purgablefile.txt', exists=False)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)
		
		self.assertGrep('pysys.out', expr='This test is executing fine')
		self.assertGrep('pysys.out', expr='Hello world - logFileContents')
		self.assertGrep('pysys.out', expr='self.output = <\\\\', contains=False) # no \\?\ prefixes
		
		