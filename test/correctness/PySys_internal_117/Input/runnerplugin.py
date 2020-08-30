import pysys

class MyRunnerPlugin:
	def setup(self, runner):
		pysys.constants.TIMEOUTS['WaitForAvailableTCPPort'] = 3
