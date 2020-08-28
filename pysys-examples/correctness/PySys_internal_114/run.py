import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, io
import json

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')

		# output directory handling with modes
		runPySys(self, 'run', ['run', '--mode=ALL'], workingDir='test')
		runPySys(self, 'print-full', ['print', '--full'], workingDir='test')
		runPySys(self, 'print-json', ['print', '--json'], workingDir='test')
		
	def validate(self):
		self.logFileContents('run.out', includes=[' [^ ]+ execution order hint = .*'], maxLines=0)
		
		with open(self.output+'/print-json.out', 'r') as f:
			jsondata = json.load(f)
		
		jsonhints = {}
		for t in jsondata:
			i = 0
			if not t['modes']:
				assert len(t['executionOrderHint'])==1, t
				jsonhints[t['id']] = t['executionOrderHint'][0]
			else:
				assert len(t['executionOrderHint']) == len(t['modes']), t
				for m in t['modes']:
					jsonhints[t['id']+'~'+m] = t['executionOrderHint'][i]
					i+=1
		
		for test, expected in [
			('Test1', '1'),
			('Test2', '2 + 10 + 50'),
			('Test3~Mode_3', '3 + -10.5'),
			('Test4~Mode_4a', '4 + 10 + 20'),
			('Test4~Mode_4b', '4 + 20 + 30 + 1*1000'),
			('Test4~Mode_4c', '4 + 20 + 2*1000'),
		]:
			self.log.info('%s: %s = %s', test, expected, eval(expected))
			self.assertThat('%s == %s', 
				float(self.getExprFromFile('run.out', '%s execution order hint = "(.*)"'%test)), eval(expected))
			self.assertThat('%s == %s', 
				jsonhints[test], eval(expected))
			self.log.info('')

		self.assertDiff('print-full.out', 'ref-print-full.out', includes=[
			'====+',
			'Test id:.*',
			'Test order hint:.*',
			'Test modes:.*',
			'Test groups:.*',
		])