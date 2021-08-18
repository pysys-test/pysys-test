from pysys.baserunner import BaseRunner
from pysys.constants import *
import logging, os

import pysys.utils.allocport

# first a quick test that we can manually change the excluded range
pysys.utils.allocport.excludedTCPPorts.add(6002)
assert 6002 not in pysys.utils.allocport.getServerTCPPorts()

# then check we can monkey patch this if we need to
def patched_getEphemeralTCPPortRange():
	raise Exception('Simulated exception getting ephemeral port range')
assert pysys.utils.allocport.getEphemeralTCPPortRange
pysys.utils.allocport.getEphemeralTCPPortRange = patched_getEphemeralTCPPortRange

class MyCustomRunner(BaseRunner):
	def setup(self):
		# should not get here
		self.log.info('Called runner.setup')