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
		ephrange = pysys.utils.allocport.getEphemeralTCPPortRange()
		self.log.info('Ephemeral port range is: %d-%d'%ephrange)
		self.assertThat('ephemeral_port_range_min < ephemeral_port_range_max', 
			ephemeral_port_range_min=ephrange[0],
			ephemeral_port_range_max=ephrange[1]
		)
		self.assertThat('ephemeral_port_range_max-ephemeral_port_range_min > 100', 
			ephemeral_port_range_min=ephrange[0],
			ephemeral_port_range_max=ephrange[1]
		)

		self.copy(self.input, self.output+'/test')

		# this has a custom runner which tries to override the default method of getting ephemeral ports
		runPySys(self, 'pysys-expect-failure', ['run'], workingDir='test', expectedExitStatus='!=0')

		runPySys(self, 'pysys-env-var', ['run', '-o', self.output+'/env-var-out'], workingDir='test', environs={'PYSYS_PORTS':'  2000 - 2020, 65000, 65020-65018 , 65040-65042 '}, defaultproject=True)
			
	def validate(self):
		self.assertGrep('pysys-expect-failure.err', expr='Simulated exception getting ephemeral port range')
		self.assertGrep('pysys-expect-failure.err', expr='Traceback')
		# should not have tried to get ephemeral range until runner init
		self.assertGrep('pysys-expect-failure.err', expr='baserunner.py.+__init__')

		self.assertDiff('env-var-out/NestedPass/server_ports.txt', 'server_ports.txt')
