from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/environment.py" % self.input
		env = {}
		env["PYSYS-USER"] = "Simon Batty"
		env["PYSYS-TEST"] = "Test variable"
		env["EMPTY-ENV"] = ""
		env["INT-ENV"] = "1"
		
		# on win32, minimal environment must have SYSTEMROOT set
		if PLATFORM=='win32': env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
		
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
		self.assertDiff("environment.out", "ref_environment.out", ignores=['SYSTEMROOT'])
