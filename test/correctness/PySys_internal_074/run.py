import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re

from pysys.utils.filecopy import filecopy

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		runPySys(self, 'makeproject', ['makeproject'])
		runPySys(self, 'makeproject-custom', ['makeproject', '--dir', self.output+'/mytestRootDir', '--template=default'])
		
		# should not overwrite even though filename is different
		open(self.mkdir(self.output+'/fakeprojroot')+'/pysysproject.xml','w').close()
		exitcode = runPySys(self, 'makeproject-alreadyexists', ['makeproject', '--dir', 'fakeprojroot'], expectedExitStatus='!=0')

		runPySys(self, 'make', ['make', 'mynewtest'])
		runPySys(self, 'run', ['run','mynewtest'])
			
	def validate(self):
		self.assertGrep('make.err', expr='.*', contains=False) # no errors
		self.assertGrep('makeproject.err', expr='.*', contains=False) # no errors
		self.assertGrep('makeproject-custom.err', expr='.*', contains=False) # no errors

		self.assertThat('os.path.isdir(%s)', repr(self.output+'/mynewtest/Input'))
		self.assertThat('os.path.isfile(%s)', repr(self.output+'/mynewtest/pysystest.xml'))
		self.assertThat('os.path.isfile(%s)', repr(self.output+'/mynewtest/run.py'))
	
		# check for correct default outcome for new tests
		self.assertGrep('run.out', expr='Test final outcome *:.*NOT VERIFIED') 
		self.assertGrep('run.out', expr='mynewtest') 
		
		# makeproject checks
		self.assertGrep('makeproject-alreadyexists.out', expr='Cannot create as project file already exists: .+')
		self.assertDiff(self.output+'/pysysproject.xml', self.output+'/mytestRootDir/pysysproject.xml')
		self.assertGrep('makeproject.out', expr='Successfully created project configuration')
		self.logFileContents('makeproject.out')

		self.assertGrep('pysysproject.xml', expr=r'<requires-pysys>\d+[.]\d+[.]\d+</requires-pysys>')
		self.assertGrep('pysysproject.xml', expr=r'<requires-python>\d+[.]\d+[.]\d+</requires-python>')
		self.assertGrep('pysysproject.xml', expr=r'@.*', contains=False) # unsubstituted tokens
		