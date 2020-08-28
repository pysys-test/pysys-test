from pysys.unit.pyunit import PyUnitTest
from pysys.constants import *
import os

class PySysTest(PyUnitTest):

	def execute(self):
		PyUnitTest.execute(self)
		if FAILED in self.outcome:
			# We're testing for failures, so we should get one
			self.outcome.remove(FAILED)
			self.outcome.append(PASSED)
		else:
			self.log.error('Expecting a failure but did not get one ... failed')
			self.outcome.append(FAILED)

	def getPythonPath(self):
		return [self.project.pyunitUtilsDir]

