from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		args = ['a1', 
			# empty string
			'', 
			'a3', 
			'arg with spaces',
			' arg with leading and trailing spaces ',
			'r*', # shell wildcard character
			' r*', # shell wildcard character and initial space
			' with \\ one backslash char',
			'with \\\\ two backslash chars',
			' with ? one question char',
			' with ?? two question chars',
			'with " double quote char',
			'with "" two double quote char',
			' with \' single quote char',
			'last arg',
			]
		self.startProcess(command=sys.executable,
						  arguments=[self.input+'/test.py']+args,
						  environs = os.environ,
						  stdout = "%s/test.out" % self.output,
						  stderr = "%s/test.err" % self.output,
						  ignoreExitStatus=False,
						  state=FOREGROUND)
		
	def validate(self):
		self.logFileContents('test.out', maxLines=0)
		self.assertDiff('test.out', 'ref_test.out')
