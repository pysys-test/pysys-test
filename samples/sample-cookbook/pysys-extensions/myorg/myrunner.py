import sys
import logging

import pysys
import pysys.baserunner

class MyRunner(pysys.baserunner.BaseRunner):
	"""
	Example of a custom runner class. 
	
	NB: usually it is better to write runner plugin(s) rather than defining a custom runner class. 
	"""

	# Parameters for the test run should be defined as class variables; the default value indicates the expected type:

	myRunnerArg = 12345
	"""
	Example of a runner configuration option. The value for this plugin instance can be overridden on the command 
	line using pysys run -Xkey=value. 
	
	Types such as boolean/list[str]/int/float will be automatically converted from string. 
	"""

	def setup(self):
		super().setup()
		self.log.info('MyRunner.setup was called; myRunnerArg=%r', self.myRunnerArg)

	def cleanup(self):
		super().cleanup()
		self.log.info('MyRunner.cleanup was called')

