import logging
import sys

import pysys

class MyRunnerPlugin(object):
	def __init__(self, runner, pluginProperties):
		self.owner = self.runner = runner
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
		
		self.log.info('Created MyRunnerPlugin instance with pluginProperties=%s', pluginProperties)
		
		pysys.utils.misc.setInstanceVariablesFromDict(self, pluginProperties, errorOnMissingVariables=True)
		self.myCmdLineOption = runner.getXArg('myorgCmdLineOption', default=True)
		if not self.myCmdLineOption: return

		# If needed, we can schedule a method to be called during cleanup from here
		runner.addCleanupFunction(self.__myPluginCleanup)

		# A runner plugin can contribute additional keys to the runner's runDetails
		# Process starting and output directory are shared with the runner
		self.owner.mkdir(self.owner.output)
		self.owner.startProcess(sys.executable, arguments=['--version'], stdouterr='MyRunnerPlugin.pythonVersion')
		pythonVersion = self.owner.waitForGrep('MyRunnerPlugin.pythonVersion.out', '(?P<output>.+)')['output'].strip()
		self.runner.runDetails['myPythonVersion'] = pythonVersion

		# Could start a server here, or provision any shared resources needed by all tests, ...
		
	
	def __myPluginCleanup(self):
		self.log.info('Cleaning up MyRunnerPlugin instance')

class MyRunnerPlugin2(MyRunnerPlugin):
	def __init__(self, runner, pluginProperties):
		self.owner = self.runner = runner
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
		
		# If needed, can get a reference to other plugins
		otherPlugin = next(plugin for plugin in runner.runnerPlugins if type(plugin).__name__=='MyRunnerPlugin')

		self.log.info('Created MyRunnerPlugin2 instance with reference to other plugin: %s', otherPlugin)
