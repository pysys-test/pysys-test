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
		
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = env,
						  workingDir = self.output,
						  stdout = "%s/environment.out" % self.output,
						  stderr = "%s/environment.err" % self.output,
						  state=BACKGROUND)

		# wait for the strings to be writen to sdtout
		self.waitForSignal("environment.out", expr="Written process environment", timeout=5)
			
	def validate(self):
		# validate against the reference file
		self.assertDiff("environment.out", "ref_environment.out")