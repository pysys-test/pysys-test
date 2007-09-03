from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/internal/utilities/scripts/counter.py" % self.project.root

		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "20", "1"],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "%s/timeout.out" % self.output,
						  stderr = "%s/timeout.err" % self.output,
						  state=FOREGROUND,
						  timeout=5)
			
	def validate(self):
		if self.getOutcome() == TIMEDOUT:
			self.log.info("Outcome list contains TIMEDOUT %s" % self.outcome)
			self.outcome = [PASSED]