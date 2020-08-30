from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
import shutil, platform

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		try:
			self.pysys.pysys('pysys', ['run', '-o', 'myoutdir', 
				'-X', 'projectbooloverride=fAlse', 
				'-X', 'cmdlineoverride=tRue',
				'-XtestBooleanProperty=tRue',
				'-XtestIntProperty=1234',
				'-XtestFloatProperty=456.78',
				'-XtestStringProperty=123456',
				'-XtestListProperty= abc  , def,,g',
				'-XtestNoneProperty=Hello',
				'-vDEBUG',
				], workingDir='test', environs={
				'TEST_USER':"Felicity Kendal",
			})
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err')
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
		
		name = '${os}_${hostname}_${startDate}_${startTime}'
		self.write_text(name+'.txt', 'xxx') # check these don't contain any non-file system characters

	def validate(self):
		# mostly checked by nested testcase, but also:
		self.assertGrep('pysys.out', expr='projectbool=True')
		self.assertGrep('pysys.out', expr='projectbooloverride=False')
		self.assertGrep('pysys.out', expr='booldeftrue=True')
		self.assertGrep('pysys.out', expr='booldeffalse=False')
		self.assertGrep('pysys.out', expr='cmdlineoverride=True')
		
		self.assertThat('prop == expected', prop__eval='self.project.os', expected=platform.system().lower())
		self.assertThat('prop != ""', prop__eval='self.project.startDate')
		self.assertThat('prop != ""', prop__eval='self.project.startTime')
		self.assertThat('prop != ""', prop__eval='self.project.hostname')
		
		self.assertGrep('pysys.out', expr='WARN .*', contains=False)
