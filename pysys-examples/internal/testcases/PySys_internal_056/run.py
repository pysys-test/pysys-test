from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.phandle = self.startProcess(command=sys.executable,
										arguments = ["%s/wait.py" % self.input],
						  				environs = os.environ,
						  				workingDir = self.input,
						  				stdout = "%s/wait.out" % self.output,
						  				stderr = "%s/wait.err" % self.output,
						  				state=BACKGROUND)

	def validate(self):
		self.assertTrue(True)
		self.assertTrue(False)
		self.waitProcess(self.phandle, timeout=1)
		self.assertTrue(True)
		self.assertGrep('not_there', expr="")
		self.checkOutcome()
		
	def checkOutcome(self):
		outcome = self.getOutcome()
		self.log.info('Outcome is %s' % self.outcome)
		self.log.info('Outcome is %s' % LOOKUP[outcome])
		
		self.outcome = [] 
		if outcome == BLOCKED: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED)
		
		