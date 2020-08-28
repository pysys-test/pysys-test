import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.xml.project import createProjectConfig
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, os.path.join(self.output,'test'))

		subtest = 'enabled-defaults'
		runPySys(self, subtest, ['run', '--record', '--threads', '1', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true'})

		subtest = 'enabled-printLogsOverride' 
		runPySys(self, subtest, ['run', '--record', '--printLogs', 'all', '--threads', '2', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true'})

		subtest = 'ci' 
		runPySys(self, subtest, ['run', '--ci', '-j1', '-o', subtest], # prevent multi-threaded else we'll have non-determnistic ordering
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true'})

		subtest = 'default-project' 
		createProjectConfig(self.mkdir(self.output+'/defconfig'))
		runPySys(self, subtest, ['run', '--record', '--printLogs', 'all', '--threads', '2', '-o', subtest], 
			workingDir='test', ignoreExitStatus=True, environs={'TRAVIS':'true', 
				'PYSYS_PROJECTFILE':self.output+'/defconfig/pysysproject.xml'})

			
	def validate(self):

		for subtest in ['enabled-defaults', 'default-project', 'ci']:
			self.assertOrderedGrep('%s.out'%subtest, exprList=[
				# first folding, using the test outdir name
				# avoid using the actual literal here else travis will try to fold it!
				'[@t]ravis_fold:[@s]tart:PySys-%s'%subtest,
				'INFO .*Id.*:.*NestedFail',
				'INFO .*Id.*:.*NestedTimedout',
				# end folding before summary
				'[@t]ravis_fold:[@e]nd:PySys-%s'%subtest,
				'Summary of failures:',
				])

		# this CI provider disables printing of non-failure logs by default
		self.assertGrep('enabled-defaults.out', expr='Id.*:.*NestedPass', contains=False)

		# but can override it explicitly if user wants to
		self.assertGrep('enabled-printLogsOverride.out', expr='Id.*:.*NestedPass', contains=True)

