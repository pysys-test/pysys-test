import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, re, shutil

class PySysTest(BaseTest):

	def execute(self):
		shutil.copytree(self.input, self.output+'/test')
		
		# TODO: enable coloring
		# enable run.log utf8
		
		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		# use multiple cycles since the buffering is different
		try:
			runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir'], workingDir=self.output+'/test')
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)

		self.assertOrderedGrep('myoutdir/NestedTest/run.log', exprList=[
			'About to print', 
			'INFO .*Hello world! unicode plain',
			'Hello world! bytes plain',
			'Hello %s',
			'INFO',
			'INFO',
			'After newlines'
		], encoding='utf-8')
		
		self.assertGrep('myoutdir/NestedTest/run.log', expr=u'Hello world! \xa3', encoding='utf-8')
