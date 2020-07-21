import sys
import logging

import pysys

class MyTestPlugin(object):
	myPluginProperty = 'foo bar'

	def __init__(self, testobj, pluginProperties):
		self.owner = self.testobj = testobj
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
		self.log.info('Created MyTestPlugin instance with pluginProperties=%s', pluginProperties)
		pysys.utils.misc.setInstanceVariablesFromDict(self, pluginProperties, errorOnMissingVariables=True)

		testobj.addCleanupFunction(self.__myPluginCleanup)
	
	def __myPluginCleanup(self):
		self.log.info('Cleaning up MyTestPlugin instance')

	# An example of providing a method that can be accessed from each test
	def getPythonVersion(self):
		self.owner.startProcess(sys.executable, arguments=['--version'], stdouterr='MyTestPlugin.pythonVersion')
		return self.owner.waitForGrep('MyTestPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()

	# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
	# That approach allows you to later customize the logic by changing just one single place, and also to omit 
	# it for specific tests where it is not wanted. 
	def checkLogsForErrors(self):
		self.assertGrep('myapp.log', ' ERROR .*', contains=False)

	# This is convenient for allowing access to the owner's methods and fields as if they were on self
	def __getattr__(self, name): return getattr(self.owner, name)
