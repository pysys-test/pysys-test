import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		import pysys.utils.allocport
		self.log.info('Ephemeral port range is: %d-%d'%pysys.utils.allocport.getEphemeralTCPPortRange())
		self.assertEval('{ephemeral_port_range_min} < {ephemeral_port_range_max}', 
			ephemeral_port_range_min=pysys.utils.allocport.getEphemeralTCPPortRange()[0],
			ephemeral_port_range_max=pysys.utils.allocport.getEphemeralTCPPortRange()[1]
		)

		shutil.copytree(self.input, self.output+'/test')

		# this has a custom runner which tries to override the default method of getting ephemeral ports
		runPySys(self, 'pysys-expect-failure', ['run'], workingDir='test', expectedExitStatus='!=0')

		runPySys(self, 'pysys-env-var', ['run'], workingDir='test', environs={'PYSYS_EPHEMERAL_TCP_PORT_RANGE':'  2000 - 2020 '}, defaultproject=True)
			
	def validate(self):
		self.assertGrep('pysys-expect-failure.err', expr='Simulated exception getting ephemeral port range')
		self.assertGrep('pysys-expect-failure.err', expr='Traceback')
		# should not have tried to get ephemeral range until runner init
		self.assertGrep('pysys-expect-failure.err', expr='baserunner.py.+__init__')

		self.assertGrep('pysys-env-var.out', expr='Ephemeral port range is: 2000-2020')
