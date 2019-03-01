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
		runPySys(self, 'pysys', ['run', '-o', self.output+'/output', '--purge'])
	
			
	def validate(self):
		self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)')
		
		self.assertThat('os.path.exists(%s)', repr(self.output+'/output/PySys_NestedTestcase/run.log'))
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/output/PySys_NestedTestcase/nonempty.txt'))
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/output/PySys_NestedTestcase/empty.txt'))
