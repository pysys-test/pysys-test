import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, json

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		if pysys.utils.pycompat.PY2: self.skipTest('this sample does not work well on PY2 as it uses stderr not stdout for printing the version')
		runPySys(self, self.output+'/pysys', ['run', '-o', self.output+'/pysys_output', '-XmyCmdLineOption=12345'], workingDir=self.input)

	def validate(self):
		self.logFileContents('pysys.out')
		
		self.assertGrep('pysys.out', expr='Created MyRunnerPlugin instance')
		self.assertGrep('pysys.out', expr='Created MyTestPlugin instance')

		self.assertGrep('pysys.out', expr="Created MyTestPlugin instance with myPluginProperty=val1")
		self.assertGrep('pysys.out', expr="Created MyTestPlugin instance with myPluginProperty=val2")
		
		self.assertLineCount('pysys.out', expr='Cleaning up MyTestPlugin instance', condition='==4') # 2 instances * 2 tests
		self.assertLineCount('pysys.out', expr='Cleaning up MyRunnerPlugin instance', condition='==1')

		# This runner adds to the runDetails
		self.assertGrep('pysys.out', expr=' myPythonVersion: .+')

		self.assertGrep('pysys.out', expr='Created MyRunnerPlugin2 instance with reference to other plugin: .*myorg.runnerplugin.MyRunnerPlugin object')