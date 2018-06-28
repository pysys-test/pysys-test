import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		
		shutil.copytree(self.input, self.output+'/test')

		exitcode = runPySys(self, 'pysys', ['run'], ignoreExitStatus=True, workingDir='test')
		self.assertThat('%d != 0', exitcode.exitStatus)
		self.logFileContents('pysys.out', maxLines=0)
		self.logFileContents('pysys.err')
			
	def validate(self):
		self.assertGrep('pysys.err', expr='Traceback')
		self.assertGrep('pysys.err', expr='customfmt.py')
		self.assertGrep('pysys.err', expr='this is a syntax error!')