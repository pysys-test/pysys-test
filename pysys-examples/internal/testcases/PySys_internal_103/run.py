from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.manual.ui import ManualTester
from pysys.utils.pycompat import PY2

class PySysTest(BaseTest):
	def execute(self):
		self.pythonDocTest(self.input+'/test.py', disableCoverage=True, 
			# this is an unfortunate hack - Python 2 and 3.5 seems broken on Ubuntu Linux 
			# due to https://bugs.launchpad.net/ubuntu/+source/python2.7/+bug/1115466 
			# and needs PYTHONPATH to be set as a workaround
			pythonPath=sys.path if PLATFORM=='linux' else None)
		
		assert self.getOutcome() == FAILED, 'expected to fail'
		reason = self.getOutcomeReason()
		self.addOutcome(PASSED, 'Doctest failed as expected', override=True)
		self.assertThat('"3 passed and 2 failed" in %s', repr(reason))
		self.assertThat('"in test.myFunction" in %s', repr(reason)) # first failure reason
		
	def validate(self):
		pass
