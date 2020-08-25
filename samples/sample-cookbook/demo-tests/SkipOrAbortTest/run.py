import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		if sys.platform in ['win32', 'linux', 'darwin']:
			# Skipping throws an exception that prevents the rest of execute/validate being invoked, and a 
			# non-failure outcome is reported.
			self.skipTest('MyFeature is not supported on this operating system')
		
		if True:
			# Any valid PySys outcome can be specified when aborting a test. 
			# The most common is BLOCKED, but others such as TIMEDOUT may be appropriate in some cases.
			self.abort(TIMEDOUT, "Test encountered a fatal problem on %s"%sys.platform)

	def validate(self):
		assert False, 'Never executed'
