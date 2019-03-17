import re
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/environment.py" % self.input
		env = {}
		env["PYSYS-USER"] = "Simon Batty"
		env["PYSYS-TEST"] = "Test variable"
		env["EMPTY-ENV"] = ""
		env["INT-ENV"] = "1"
		#env["PYTHONPATH"] = os.pathsep.join(sys.path)

		
		if PLATFORM=='win32':
			# on win32, minimal environment must have SYSTEMROOT set
			env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
		elif PLATFORM=='linux' or PLATFORM=='solaris':
			# On UNIX we may need the python shared libraries on the LD_LIBRARY_PATH
			env["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH",'')
		
		# create the process
		self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = env,
						  workingDir = self.output,
						  stdout = 'environment-specified.out',
						  stderr = 'environment-specified.err',
						  ignoreExitStatus=False, abortOnError=True, 
						  state=FOREGROUND)

		self.startProcess(command=sys.executable,
						  arguments = [script],
						  # don't set environs=
						  workingDir = self.output,
						  stdout = 'environment-default.out',
						  stderr = 'environment-default.err',
						  ignoreExitStatus=False, abortOnError=True, 
						  state=FOREGROUND)
		self.logFileContents('environment-default.out')

		# wait for the strings to be writen to stdout (not sure why, should be instant); 
		# also serves as a verification that they completed successfully
		self.waitForSignal("environment-specified.out", expr="Written process environment", timeout=5, abortOnError=True)
		self.waitForSignal("environment-default.out", expr="Written process environment", timeout=5, abortOnError=True)

	def validate(self):
		# validate against the reference file

		ignores=['SYSTEMROOT','LD_LIBRARY_PATH']#, 'PYTHONPATH']
		
		if PLATFORM=='darwin':
			ignores.append('VERSIONER_PYTHON')
			ignores.append('__CF_USER_TEXT_ENCODING')
		# also ignore env vars that Pythong sometimes sets on itself
		ignores.append('LC_CTYPE')

		self.assertDiff("environment-specified.out", "ref_environment.out", ignores=ignores)

		# check we haven't copied any env vars from the parent environment other than the expected small minimal set
		envvarignores = ['TEMP.*', 'TMP=']+['^%s='%x.upper() for x in 
			['ComSpec', 'OS', 'PATHEXT', 'SystemRoot', 'SystemDrive', 'windir', 'NUMBER_OF_PROCESSORS']+[
				'LD_LIBRARY_PATH', 'PATH']+ignores]
		self.assertGrep('environment-default.out', expr='.*=', contains=False, ignores=envvarignores)
		