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

		subtest = 'test-project'
		runPySys(self, subtest, ['run', '-o', subtest], 
			workingDir='test', expectedExitStatus='!=0', environs={'GITHUB_ACTIONS':'true'}, background=True)

		subtest = 'default-project' 
		createProjectConfig(self.mkdir(self.output+'/defconfig'))
		runPySys(self, subtest, ['run', '--ci', '-o', subtest], 
			workingDir='test', expectedExitStatus='!=0', environs={'GITHUB_ACTIONS':'true', 
				'PYSYS_PROJECTFILE':self.output+'/defconfig/pysysproject.xml'}, background=True)

		self.waitForBackgroundProcesses()
			
	def validate(self):
		for subtest in ['test-project', 'default-project']:
			self.assertGrep(subtest+'.err', expr='.+', contains=False)
			self.assertGrep(subtest+'.out', expr='(Traceback.*|caught .*)', contains=False)
			self.assertOrderedGrep('%s.out'%subtest, exprList=[
				# first folding, using the test outdir name
				'^::group::Logs for test run: %s'%subtest,
				'INFO .*Id.*:.*NestedFail',
				# end folding before summary
				'^::endgroup::',
				'^::group::[(]GitHub test failure annotations[)]',
				'^::error file=.*/pysysproject.xml::Failure outcomes: 2 TIMED OUT, 1 FAILED.*%0A.*Summary of failures: ',
				
				'^::warning file=.*/run.py',
				'^::endgroup::',
				])


		# this CI provider disables printing of non-failure logs by default
		self.assertGrep('test-project.out', expr='Id.*:.*NestedPass', contains=False)

		# outputs (to enable artifact uploading) are only set when we ran with --ci (i.e. --record)
		self.assertGrep('default-project.out', expr='^::set-output name=artifact_TestOutputArchiveDir::..................*/__pysys_output_archives')
		self.assertGrep('test-project.out', expr='^::set-output', contains=False)

		self.assertGrep('default-project.out', expr='^::warning file=.*/run.py,line=7::.*Id.*NestedTimedout2%0A.*Test duration:') # includes line number
		self.assertLineCount('default-project.out', expr='::(warning|error)', condition='==4')
		self.assertLineCount('test-project.out', expr='::(warning|error)', condition='==3') # =4 minus the one GitHub adds for the non-zero exit code
		self.assertGrep('test-project.out', expr='(annotation limit reached; for any additional test failures, see the detailed log)', literal=True)

