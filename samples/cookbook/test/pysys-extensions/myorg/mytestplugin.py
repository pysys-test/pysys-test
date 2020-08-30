import sys
import logging

import pysys

class MyTestPlugin(object):
	""" Example of a test plugin. 
	
	An instance of each test plugin is constructed for each test object. Tests can access the methods and fields of 
	their plugin using the alias specified in the project configuration (e.g. self.<alias>.). 
	
	"""
	
	# Plugin properties should be defined as class variables; the default value indicates the expected type:

	myPluginProperty = 999
	"""
	Example of a plugin configuration property. The value for this plugin instance can be overridden using ``<property .../>``.
	Types such as boolean/list[str]/int/float will be automatically converted from string. 
	"""

	def setup(self, testObj):
		# setup() is the only method a plugin must provide, and is called just after the BaseTest object is created.
		
		self.owner = self.testObj = testObj

		self.log = logging.getLogger('pysys.myorg.MyTestPlugin')
		self.log.info('MyTestPlugin.setup called; myPluginProperty=%r', self.myPluginProperty)
		self.log.info('')

		# there is no standard cleanup() method, so do this if you need to execute something on cleanup:
		testObj.addCleanupFunction(self.__myPluginCleanup)
	
	def __myPluginCleanup(self):
		pass
		# This would be a good place to perform a graceful shutdown of any processes started by this plugin, 
		# in case you want to check graceful shutdown works, or if it's needed to get code coverage results (any 
		# remaining processes are automatically killed later, so no need to worry about killing processes here)

	# An example of providing a method that can be accessed from each test
	def getPythonVersion(self):
		"""
		Example of a method that can be called by individual tests using this plugin. 
		"""
		self.owner.startProcess(pysys.constants.PYTHON_EXE, arguments=['--version'], stdouterr='MyTestPlugin.pythonVersion')
		return self.owner.waitForGrep('MyTestPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()

	# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
	# That approach allows you to later customize the logic by changing just one single place, and also to omit 
	# it for specific tests where it is not wanted. 
	def checkLog(self, logfile='my_server.out', ignores=[]):
		"""
		Asserts that the specified log file does not contain any errors. 
		"""
		self.assertGrep(logfile, ' (ERROR|FATAL) .*', contains=False, 
			ignores=ignores or ['ERROR .*Expected error'])

	# This is convenient for allowing access to the owner's methods and fields as if they were on self; e.g. "self.assertGrep"
	def __getattr__(self, name): return getattr(self.owner, name)
