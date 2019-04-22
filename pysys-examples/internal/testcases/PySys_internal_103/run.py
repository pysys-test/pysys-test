from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.manual.ui import ManualTester

class PySysTest(BaseTest):
	def execute(self):
		self.pythonDocTest(self.input+'/test.py', disableCoverage=True)

		# temp debugging:
		import pysys
		self.pythonDocTest(self.input+'/test.py')

		self.pythonDocTest(self.input+'/test.py', disableCoverage=True, pythonPath=sys.path)
		
		self.pythonDocTest(os.path.dirname(pysys.__file__)+'/process/user.py', 
			pythonPath=sys.path)

		
		assert self.getOutcome() == FAILED, 'expected to fail'
		reason = self.getOutcomeReason()
		self.addOutcome(PASSED, 'Doctest failed as expected', override=True)
		self.assertThat('"3 passed and 2 failed" in %s', repr(reason))
		self.assertThat('"in test.myFunction" in %s', repr(reason)) # first failure reason
		
	def validate(self):
		pass
