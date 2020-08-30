import re, sys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		self.log.info('Using python from     %s', sys.executable)
		self.log.info('With python libs from %s', os.__file__)

		script = "%s/environment.py" % self.input
		env = {}
		env["PYSYS-USER"] = "Simon Batty"
		env["PYSYS-TEST"] = "Test variable"
		env["EMPTY-ENV"] = ""
		env["INT-ENV"] = "1"

		# this mirrors the logic we use in createEnvirons for sys.executable
		if PLATFORM=='win32':
			# on win32, minimal environment must have SYSTEMROOT set
			env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
		else:
			# On UNIX we may need the python shared libraries on the LD_LIBRARY_PATH
			env[LIBRARY_PATH_ENV_VAR] = (os.environ.get(LIBRARY_PATH_ENV_VAR,'')).strip(os.pathsep)
		env['PATH'] = os.path.dirname(sys.executable)+os.pathsep+PATH
		
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
		self.waitForGrep("environment-specified.out", expr="Written process environment", timeout=5, abortOnError=True)
		self.waitForGrep("environment-default.out", expr="Written process environment", timeout=5, abortOnError=True)

	def validate(self):
		# validate against the reference file

		ignores=['SYSTEMROOT','PYTHONHOME', LIBRARY_PATH_ENV_VAR, 'PATH']
		
		if PLATFORM=='darwin':
			ignores.append('VERSIONER_PYTHON')
			ignores.append('__CF_USER_TEXT_ENCODING')
			ignores.append('__PYVENV.*')
		# also ignore env vars that Pythong sometimes sets on itself
		ignores.append('LC_CTYPE')

		self.assertDiff("environment-specified.out", "ref_environment.out", ignores=ignores)
		self.assertGrep("environment-specified.out", expr='PATH=.+')

		# check we haven't copied any env vars from the parent environment other than the expected small minimal set
		envvarignores = []
		envvarignores.extend(['TEMP.*', 'TMP.*=']) # set in default pysys config file

		if IS_WINDOWS:
			envvarignores.extend(['ComSpec', 'OS', 'PATHEXT', 'SystemRoot', 'SystemDrive', 'windir', 
				'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
				'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 
				'SYSTEM', 'SYSTEM32'])

		envvarignores.extend(['^%s='%x.upper() for x in 
			['ComSpec', 'OS', 'PATHEXT', 'SystemRoot', 'SystemDrive', 'windir', 'NUMBER_OF_PROCESSORS']+[
				'LD_LIBRARY_PATH', LIBRARY_PATH_ENV_VAR, 'PATH']+ignores])
		if not IS_WINDOWS: envvarignores.append('LANG=en_US.UTF-8') # set in default pysys config file
		self.assertGrep('environment-default.out', expr='.*=', contains=False, ignores=envvarignores)
		
