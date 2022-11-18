__pysys_title__   = r""" Demo of using a test plugin called MyTestPlugin to check log for errors """
#                        ===============================================================================
__pysys_purpose__ = r""" 
	"""

__pysys_authors__ = "pysysuser"
__pysys_created__ = "1999-12-31"

import pysys.basetest, pysys.mappers
from pysys.constants import *
from myorg.mytesthelper import CookbookSampleHelper

class PySysTest(CookbookSampleHelper, pysys.basetest.BaseTest):
	def execute(self):
		# Due to inheriting CookbookSampleHelper, we can access method and fields of our helper using self.cookbook.XXX
		self.log.info('Used CookbookSampleHelper to get Python version: %s', self.cookbook.getPythonVersion())

		self.write_text('my_server.out', 'No errors here')

	def validate(self):
		# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
		# That approach allows you to later customize the logic by changing just one single place, and also to omit 
		# it for specific tests where it is not wanted. 
		self.cookbook.checkLog('my_server.out')
	