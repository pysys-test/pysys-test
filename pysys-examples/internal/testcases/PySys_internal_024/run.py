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
		env["PYTHONPATH"] = os.pathsep.join(sys.path)

		
		if PLATFORM=='win32':
			# on win32, minimal environment must have SYSTEMROOT set
			env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
		elif PLATFORM=='linux' or PLATFORM=='solaris':
			# On UNIX we may need the python shared libraries on the LD_LIBRARY_PATH
			env["LD_LIBRARY_PATH"] = os.environ.get("LD_LIBRARY_PATH",'')
		
		# create the process
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = env,
						  workingDir = self.output,
						  stdout = os.path.join(self.output, 'environment.out'),
						  stderr = os.path.join(self.output, 'environment.err'),
						  state=FOREGROUND)

		# wait for the strings to be writen to sdtout
		self.waitForSignal("environment.out", expr="Written process environment", timeout=5)
			
	def validate(self):
		# validate against the reference file

		ignores=['SYSTEMROOT','LD_LIBRARY_PATH', 'PYTHONPATH']
		
		if PLATFORM=='darwin':
			ignores.append('VERSIONER_PYTHON')
			ignores.append('__CF_USER_TEXT_ENCODING')
			ignores.append('__PYVENV.*')
		# also ignore env vars that Pythong sometimes sets on itself
		ignores.append('LC_CTYPE')

		self.assertDiff("environment.out", "ref_environment.out", ignores=ignores)
