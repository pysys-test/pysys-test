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
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'x', ['print', 'x'], workingDir='test', expectedExitStatus='==10')
		runPySys(self, 'Prefix', ['print', 'Prefix'], workingDir='test')
		runPySys(self, 'Suffix', ['print', 'Suffix'], workingDir='test') # without any id-prefix, this is an exact match
		
		# the order is a bit different when we have an id prefix
		self.write_text(self.output+'/test/pysysdirconfig.xml', u"""<?xml version="1.0" standalone="yes"?>
<pysysdirconfig>
	<id-prefix>ID_PREFIX.</id-prefix>
</pysysdirconfig>
		""")
		runPySys(self, 'x-idpref', ['print', 'x'], workingDir='test', expectedExitStatus='==10')
		runPySys(self, 'Prefix-idpref', ['print', 'Prefix'], workingDir='test')
		
		# Suffix is an exact match for the testDir basename (even though it's not for the testId)
		runPySys(self, 'Suffix-idpref', ['print', 'Suffix'], workingDir='test')
		
		# there are two matching tests
		runPySys(self, 'Numbered', ['print', '1'], workingDir='test', expectedExitStatus='==10')

		# check handling of a test named 0 works OK (given we strip leading zeros)
		runPySys(self, 'Numbered0', ['print', '00'], workingDir='test')

		runPySys(self, 'all-idpref', ['print'], workingDir='test')

		
	def validate(self):
		self.logFileContents('all-idpref.out', maxLines=0) # useful to see everything
		for f in ['x.err', 'Prefix.out', 'Suffix.out', 'x-idpref.err', 'Prefix-idpref.out', 'Suffix-idpref.out', 'Numbered.err', 'Numbered0.out']:
			self.logFileContents(f)
			self.assertDiff(f)
