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

		if self.getOutcome() !=NOTVERIFIED: self.abort(FAILED, 'Test should not have failed at this point')

	def validate(self):
		self.assertTrue(True)
		self.assertTrue(False)
		try:
			self.waitProcess(self.phandle, timeout=1, abortOnError=True)
			self.addOutcome(BLOCKED, 'unexpected error - should have aborted')
		except Exception as e:
			self.outcome=[]
			self.addOutcome(TIMEDOUT, 'Simulated timeout')
		self.assertTrue(False)
		self.assertTrue(True)
		self.checkOutcome()
		
	def checkOutcome(self):
		outcome = self.getOutcome()
		self.log.info('Outcome is %s' % self.outcome)
		self.log.info('Outcome is %s' % LOOKUP[outcome])

		self.outcome = [] 
		if outcome == TIMEDOUT: self.addOutcome(PASSED)
		else: self.addOutcome(FAILED, 'was expecting TIMEDOUT outcome but got %s'%LOOKUP[outcome])
		
		
