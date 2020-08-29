import logging
import sys

import pysys

class MyRunnerPlugin(object):
	""" Example of a runner plugin. 
	
	A single instance of each runner plugin is constructed by the singleton test runner class. Tests can access the 
	methods and fields of runner plugins using ``self.runner.<alias>`` if an alias is specified in the project 
	configuration.
	
	"""

	# Plugin properties should be defined as class variables; the default value indicates the expected type:
	
	myPluginProperty = False
	"""
	Example of a plugin configuration property. The value for this plugin instance can be overridden using ``<property .../>``.
	Types such as boolean/list[str]/int/float will be automatically converted from string. 
	"""

	def setup(self, runner):
		# setup() is the only method a plugin must provide, and is called just before BaseRunner.setup is called.
		
		self.owner = self.runner = runner
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
		
		# This shows how you can access both plugin properties and command line -X options. 
		self.log.info('MyRunnerPlugin.setup called; myPluginProperty=%r and myArg=%r', 
			self.myPluginProperty, runner.getXArg('myCmdLineOption', default=123))

		# If needed, we can schedule a method to be called during runner cleanup from here.
		runner.addCleanupFunction(self.__myPluginCleanup)

		# Process starting and output directory are shared with the runner.
		self.owner.mkdir(self.owner.output)
		self.owner.startProcess(pysys.constants.PYTHON_EXE, arguments=['--version'], stdouterr='MyRunnerPlugin.pythonVersion')
		# This variable can be accessed from tests
		self.pythonVersion = self.owner.waitForGrep('MyRunnerPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()

		# A runner plugin can contribute additional keys to the runner's runDetails.
		# For example you could read the build number of the app being tested in here (e.g. with loadProperties()).
		self.runner.runDetails['myPythonVersion'] = self.pythonVersion

		# A runner plugin's setup method is the one place you can change global constants (e.g. timeouts) that will 
		# affect all tests. You can't do it from a test plugin or individual tests as that would introduce race 
		# conditions. 
		if pysys.constants.IS_WINDOWS: 
			pysys.constants.TIMEOUTS['WaitForAvailableTCPPort'] *= 2

		# This would be a good place to start a server/VM/DB that's shared by all tests, or provision shared resources, etc		
		self.log.info('') 

	def __myPluginCleanup(self):
		self.log.info('MyRunnerPlugin cleanup called')
		# This would be a good place to perform a graceful shutdown of any servers shared by the tests (any 
		# remaining processes are automatically killed later so no need to do process killing here)

class MyRunnerPlugin2(MyRunnerPlugin):
	def setup(self, runner):
		self.owner = self.runner = runner
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin2')
		
		# If needed, can get a reference to other plugins using runner.runnerPlugins
		otherPlugin = next(plugin for plugin in runner.runnerPlugins if type(plugin).__name__=='MyRunnerPlugin')

		self.log.info('Created MyRunnerPlugin2 instance with reference to other plugin: %s', otherPlugin)
