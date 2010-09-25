from pysys.unit.junit import JUnitTest
from pysys.constants import *
import os

class PySysTest(JUnitTest):
	def execute(self):
		self.compileJavaFiles(os.path.join(self.project.root, 'junit', 'utilities'), ['totest/Broken.java'])
		JUnitTest.execute(self)
		if FAILED in self.outcome:
			# We're testing for failures, so we should get one
			self.outcome.remove(FAILED)
			self.outcome.append(PASSED)
		else:
			self.log.error('Expecting a failure but did not get one ... failed')
			self.outcome.append(FAILED)

