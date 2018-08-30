# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')
		# make rootdir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '--record', '--cycle', '2'], workingDir='test', ignoreExitStatus=True)
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.out', expr='(Traceback.*|caught .*)', contains=False)
		
		# we didn't enable progress writers so there should be none here
		self.assertGrep('pysys.out', expr='--- Progress', contains=False)

		self.assertGrep('testsummary.csv', expr='id, title, cycle, startTime, duration, outcome')
		self.assertGrep('testsummary.csv', expr='NestedPass,"Nested testcase",1,[^,]+,[^,]+,PASSED')
		self.assertGrep('testsummary.csv', expr='NestedPass,"Nested testcase",2,[^,]+,[^,]+,PASSED')

		self.assertOrderedGrep('testsummary.log', exprList=[
			'PLATFORM: *[^ ]+',
			'Cycle 1',
			'FAILED: NestedFail',
			'PASSED: NestedPass',
			'Cycle 2',
			'FAILED: NestedFail'
		])
		
		self.assertGrep('testsummary.xml', expr='<descriptor>file://', encoding='utf-8') # because we enabled filed URLS
		self.assertGrep('testsummary.xml', expr='<?xml-stylesheet href="./my-pysys-log.xsl"', encoding='utf-8')
		self.assertOrderedGrep('testsummary.xml', exprList=[
			'<results cycle="1">',
			'id="NestedPass" outcome="PASSED"',
			'<outcomeReason>Reason for timed out outcome is general tardiness - %s</outcomeReason>'%TEST_STR,
			'<results cycle="2">',
			], encoding='utf-8')


		self.assertGrep('target/pysys-reports/TEST-NestedPass.1.xml', expr='failures="0" name="NestedPass" skipped="0" tests="1"', encoding='utf-8')
		self.assertGrep('target/pysys-reports/TEST-NestedPass.2.xml', expr='failures="0" name="NestedPass" skipped="0" tests="1"', encoding='utf-8')
		self.assertGrep('target/pysys-reports/TEST-NestedTimedout.1.xml', expr='failures="1" name="NestedTimedout" skipped="0" tests="1"', encoding='utf-8')
		self.assertGrep('target/pysys-reports/TEST-NestedTimedout.1.xml', expr='<failure message="TIMED OUT">Reason for timed out outcome is general tardiness - %s</failure>'%TEST_STR, encoding='utf-8')
		
		datedtestsum = glob.glob(self.output+'/testsummary-*.log')
		if len(datedtestsum) != 1: self.addOutcome(FAILED, 'Did not find testsummary-<year>.log')

		self.assertLineCount('pysys.out', expr='Summary of non passes', condition='==1')
		self.assertOrderedGrep('pysys.out', exprList=[
			'Summary of non passes: ',
			'CYCLE 1.*TIMED OUT.*NestedTimedout',
			'Reason for timed out outcome is general tardiness - %s'%(
				# stdout seems to get written in utf-8 not local encoding on python2 for some unknown reason, so skip verification of extra chars on that version; 
				# for python 3 we can do the full verification
				'Hello' if sys.version_info[0] == 2 else TEST_STR),
			'CYCLE 1.*FAILED.*NestedFail',
			'CYCLE 2.*TIMED OUT.*NestedTimedout',
		])
