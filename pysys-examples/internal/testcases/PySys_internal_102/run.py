import os, sys, math, shutil, glob, io, zipfile
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.log.info('output=%r', self.output)
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output', '--purge'], workingDir='test', 
			onError=lambda process: [self.logFileContents(process.stdout), self.logFileContents(process.stderr)] )
		# run a recond time to prove earlier files aren't kept
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output', '--purge', '--cycle', '2'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		
		with io.open(self.output+'/collected_files.txt', 'w', encoding='utf-8') as f:
			for c in sorted(os.listdir(self.output+'/pysys-output/mydir-pysys-output')):
				f.write(os.path.basename(c)+u'\n')

	def validate(self):
		self.logFileContents('collected_files.txt')
		self.assertDiff('collected_files.txt', 'ref_collected_files.txt')
		self.assertGrep('pysys.out', expr=r'Collected .+ test output files to directory: .*mydir-pysys-output$')
		self.assertGrep('pysys.out', expr=r'Collected .+ test output files to directory: .*mydir2[/\\]\d\d\d\d-\d\d-\d\d_\d\d.\d\d.\d\d')
		mydirs = glob.glob(self.output+'/mydir2/*')[0]
		self.assertPathExists(mydirs+'/1.myfile')
		self.assertPathExists(mydirs+'/2.myfile')
		
		self.assertPathExists('pysys-output/mywriter_defaultpattern/NestedTest.cycle001.a-foo.1.myext') # extension at the end after unique id
		
		# -b excluded by regex filter
		self.assertPathExists('pysys-output/mywriter_defaultpattern/NestedTest.cycle001.foo-b.1')
		self.assertThat('actual == []', actual__eval='import_module("glob").glob(self.output+"/pysys-output/mywriter-pysys-output/mydir/*foo-b*")')
		self.assertPathExists('pysys-output/mywriter-pysys-output/mydir/NestedTest.cycle001.a-foo.1.myext')
		
		with zipfile.ZipFile(self.output+'/pysys-output/mywriter-pysys-output/myArchive.zip') as zf:
			self.assertThat('badZipFiles is None', badZipFiles=zf.testzip())
			members = sorted(zf.namelist())
		self.assertThat('members == expected', members=sorted(members), expected=sorted([
			'mydir/NestedTest.cycle001.a-foo.1.myext', 
			'mydir/NestedTest.cycle001.a-foo.2.myext', 
			'mydir/NestedTest.cycle001.foo.1', 
			'mydir/NestedTest.cycle001.foo.2', 
			'mydir/NestedTest.cycle002.a-foo.1.myext', 
			'mydir/NestedTest.cycle002.a-foo.2.myext', 
			'mydir/NestedTest.cycle002.foo.1', 
			'mydir/NestedTest.cycle002.foo.2']))
