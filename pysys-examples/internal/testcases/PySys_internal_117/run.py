import os, sys, math, shutil
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		
		ports = [self.getNextAvailableTCPPort() for i in range(5)]
		self.write_text('allocated-ports.txt', '\n'.join(str(p) for p in ports)+'\n')
		
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output'], workingDir='test', 
			environs={'PYSYS_PORTS_FILE':self.output+'/allocated-ports.txt'})
		self.logFileContents('pysys.out', maxLines=0)

			
	def validate(self):
		self.assertDiff('pysys-output/NestedTest/got-ports.txt', self.output+'/allocated-ports.txt', sort=True)
		self.assertGrep('pysys.out', expr='Port allocation failed: .*Timed out trying to allocate a free TCP server port after .+ secs; other tests are currently using all the available ports.*')