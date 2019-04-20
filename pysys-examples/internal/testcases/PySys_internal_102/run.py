import os, sys, math, shutil, glob, io
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output', '--purge'], workingDir='test')
		# run a recond time to prove earlier files aren't kept
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output', '--purge', '--cycle', '2'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		
		with io.open(self.output+'/collected_files.txt', 'w', encoding='utf-8') as f:
			for c in sorted(os.listdir(self.output+'/test/mydir-pysys-output')):
				f.write(os.path.basename(c)+u'\n')

	def validate(self):
		self.logFileContents('collected_files.txt')
		self.assertDiff('collected_files.txt', 'ref_collected_files.txt')
		self.assertGrep('pysys.out', expr=r'Collected test output to directory: .*mydir-pysys-output$')
		self.assertGrep('pysys.out', expr=r'Collected test output to directory: .*mydir2[/\\]\d\d\d\d-\d\d-\d\d_\d\d.\d\d.\d\d')
		mydirs = glob.glob(self.output+'/mydir2/*')[0]
		self.assertPathExists(mydirs+'/1.myfile')
		self.assertPathExists(mydirs+'/2.myfile')