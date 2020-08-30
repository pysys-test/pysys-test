from pysys.unit.pyunit import PyUnitTest
import os

class PySysTest(PyUnitTest):

	def getPythonPath(self):
		return [os.path.join(self.project.pyunitUtilsDir)]
