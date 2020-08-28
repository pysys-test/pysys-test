import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		# We can access method and fields of our test plugin using self.alias.XXX
		self.log.info('Used mytestplugin to get Python version: %s', self.mytestplugin.getPythonVersion())

		self.write_text('my_server.out', 'No errors here')

	def validate(self):
		# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
		# That approach allows you to later customize the logic by changing just one single place, and also to omit 
		# it for specific tests where it is not wanted. 
		self.mytestplugin.checkLog('my_server.out')
	