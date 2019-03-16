import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		
		shutil.copytree(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '--record', '--threads', '2', '-o', 'pysys-output'], workingDir='test')
		self.logFileContents('pysys.out', maxLines=0)
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		# ensure these appear at start of the line, which for some CI writers is important
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^stdoutPrint-CUSTOMWRITER-setup')
		
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-processResult')
		self.assertGrep('pysys.out', expr='^sys.stdout.write-CUSTOMWRITER-setup')
		