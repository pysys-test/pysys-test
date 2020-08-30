from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import os

class PySysTest(BaseTest):
	def execute(self):
		test = self.allocateUniqueStdOutErr('test')
		p = self.startProcess(command=sys.executable,
										arguments = ["%s/wait.py" % self.input],
						  				environs = os.environ,
						  				workingDir = self.input,
						  				stdout = test.stdout,
						  				stderr = test.stderr,
						  				state=BACKGROUND, abortOnError=False)
		try:
			self.waitForGrep(test.stdout, expr='foo', process=p, abortOnError=True)
			self.addOutcome(FAILED, 'Expected abort')
		except AbortExecution as e:
			self.assertThat('%s == %s', e.outcome, BLOCKED)
			self.assertThat('"due to process '+os.path.basename(sys.executable)+' termination" in %s', repr(e.value))

	def validate(self):
		pass
