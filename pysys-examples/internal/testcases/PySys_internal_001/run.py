from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 
import shutil

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')
		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		try:
			runPySys(self, 'pysys', ['run', '-o', 'myoutdir'], workingDir='test', environs={
				'TEST_USER':"Felicity Kendal"
			})
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err')
		self.assertGrep('pysys.out', expr='XXTest final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)

	def validate(self):
		pass # checked by nested testcase