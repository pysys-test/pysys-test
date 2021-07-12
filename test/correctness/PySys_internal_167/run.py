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
		for subtest in ['badpattern', 'emptypattern', 'differentparamkeys', 'wrongparamvalue']:
			runPySys(self, subtest, ['print', '--full'], expectedExitStatus='!=0', workingDir=self.input+'/'+subtest)

	def validate(self):
		self.assertThatGrep('badpattern.err', '.+', 'value.startswith(expected)', 
			expected="ERROR: Failed to populate modeNamePattern \"{param1}_{unknownparam}\" with parameters {'param1': 'x', 'param2': 'y'}: 'unknownparam' in \"")

		self.assertThatGrep('emptypattern.err', '.+', 'value.startswith(expected)', 
			expected="ERROR: Invalid mode: cannot be empty in \"")

		self.assertThatGrep('differentparamkeys.err', '.+', 'value.startswith(expected)', 
			expected="ERROR: The same mode parameter keys must be given for each mode under <modes>, but found ['param1', 'param2'] != ['param1'] in \"")

		self.assertThatGrep('wrongparamvalue.err', '.+', 'value.startswith(expected)', 
			expected="ERROR: Cannot redefine mode \"MyMode\" with parameters {'paramName': 'wrongValue'} different to previous parameters {'paramName': 'inheritedValue'} in \"")
