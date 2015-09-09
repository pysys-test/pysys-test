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
		
		if PLATFORM=='win32':
			# on win32, minimal environment must have SYSTEMROOT set
			env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
		elif PLATFORM=='linux' or PLATFORM=='solaris':
			# On UNIX we may need the python shared libraries on the LD_LIBRARY_PATH
			env["LD_LIBRARY_PATH"] = os.environ["LD_LIBRARY_PATH"]
		
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

		ignores=['SYSTEMROOT','LD_LIBRARY_PATH']
		if PLATFORM=='darwin':
			ignores.append('VERSIONER_PYTHON')
			ignores.append('__CF_USER_TEXT_ENCODING')

		self.assertDiff("environment.out", "ref_environment.out", ignores=ignores)
