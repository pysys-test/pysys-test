import pysys
from pysys.unit.pyunit import PyUnitTest

class PySysTest(PyUnitTest):
	pass

	# Optionally you can specify extra paths to make available when running the test here (if not needed, delete this):
	def getPythonPath(self):
		return [self.input+'/test_application']
