from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	TEST_ARGS = ['a1', 
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

			# some characters have special meaning to windows cmd.exe 
			# - check that when passed through a bat script back to a normal process (in this case python) they have the same values
			'with chevrons>>chars',
			'with chevrons>>chars and " quote',
			'with redirection & char',
			'with double ampersand && chars',
			'with pipe | char',
			'with caret ^ char',
			'with double caret ^^ chars',
			'with comma, char',
			'last arg',
			]

	def execute(self):

		self.write_text('expected-args.txt', '\n'.join('arg: <%s>'%a for a in self.TEST_ARGS))
		self.startProcess(command=sys.executable,
					arguments=[self.input+'/test.py']+self.TEST_ARGS,
					environs = os.environ,
					stdouterr = "test")

		if IS_WINDOWS:
			# on windows we need to additionally test that the cmd.exe processor understands parameters the same way; 
			# if escaping of the pipes/redirections is wrong the following process may actually fail
			self.write_text('window_bat_script.bat', '\n'.join([
				'@echo Received shell arguments: %*',
				f'\n@"{sys.executable}" "{self.input}\\test.py" %*']))
			self.startProcess(command=self.output+'/window_bat_script.bat',
							arguments=self.TEST_ARGS,
							environs = os.environ,
							stdouterr='window_bat_script')

	def validate(self):
		self.logFileContents('test.out', maxLines=0)
		self.assertDiff('test.out', self.output+'/expected-args.txt')

		if IS_WINDOWS: 
			self.assertDiff('window_bat_script.out', self.output+'/expected-args.txt', ignores=['Received shell arguments.*'])
			for arg in self.TEST_ARGS:
				self.assertThatGrep('window_bat_script.out', 'Received shell arguments: (.*)', 'arg in value', 
					# cmd.exe escaping doubles up the quotes so this is acceptable
					arg=arg.replace('"', '""'))

