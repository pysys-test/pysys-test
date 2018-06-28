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
		
		for subtest in ['customformat', 'customclass']:
			shutil.copytree(self.input, self.output+'/'+subtest)
			os.rename(self.output+'/'+subtest+'/pysysproject-%s.xml'%subtest, self.output+'/'+subtest+'/pysysproject.xml')
	
			runPySys(self, subtest+'_pysys', ['run', '-o', self.output+'/'+subtest+'_output'], workingDir=subtest)
			self.logFileContents(subtest+'_pysys.out', maxLines=0)
			self.logFileContents(subtest+'_output/PySys_NestedTestcase/run.log')
			self.logFileContents(subtest+'_pysys.err')
			self.assertGrep(subtest+'_pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		
		self.assertGrep('customformat'+'_pysys.out', expr=r'STDOUT_DATE_FORMAT \d\d\d\d-\d\d.*STDOUT_PREFIX Sample log message')
		self.assertGrep('customformat_output/PySys_NestedTestcase/run.log', expr=r'\d\d\d\d-\d\d.*RUNLOG_PREFIX Sample log message')
		
		self.assertGrep('customclass'+'_pysys.out', expr=r'CUSTOM_STDOUT_PREFIX \d\d\d\d-\d\d.*Sample log message')
		self.assertGrep('customclass_output/PySys_NestedTestcase/run.log', expr=r'CUSTOM_RUNLOG_PREFIX \d\d\d\d-\d\d.*Sample log message')

