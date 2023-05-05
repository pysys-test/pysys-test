__pysys_title__   = r""" Demo of running a Python PyUnit test from PySys """
#                        ===============================================================================
__pysys_purpose__ = r""" 
	"""

__pysys_authors__ = "pysysuser"
__pysys_created__ = "1999-12-31"

__pysys_groups__  = "pyunit, unitTest"

import pysys
from pysys.unit.pyunit import PyUnitTest

class PySysTest(PyUnitTest):
	pass

	# Optionally you can specify extra paths to make available when running the test here (if not needed, delete this):
	def getPythonPath(self):
		return [self.input+'/test_application']
