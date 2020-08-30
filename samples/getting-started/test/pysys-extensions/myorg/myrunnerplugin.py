import sys
import os
import json
import logging

import pysys

class MyServerRunnerPlugin(object):
	"""
	This is a sample PySys runner plugin. 
	"""

	def setup(self, runner):
		self.owner = self.runner = runner
		self.log = logging.getLogger('pysys.myorg.MyRunnerPlugin')
		
		# During the runner setup phase (before any tests being) is a good time to add metadata about the test run, 
		# such as which version of our application we're testing with.
		runner.runDetails['myServerBuildNumber'] = pysys.utils.fileutils.loadProperties(
			runner.project.appHome+'/build.properties')['buildNumber']

