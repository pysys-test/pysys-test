import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')
		# make rootdir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read()) # define runPySys
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
		
		self.assertGrep('testsummary.xml', expr='<descriptor>file://') # because we enabled filed URLS
		self.assertGrep('testsummary.xml', expr='<?xml-stylesheet href="./my-pysys-log.xsl"')
		self.assertOrderedGrep('testsummary.xml', exprList=[
			'<results cycle="1">',
			'id="NestedPass" outcome="PASSED"',
			'<outcomeReason>Reason for timed out outcome is general tardiness</outcomeReason>',
			'<results cycle="2">',
			])


		self.assertGrep('target/pysys-reports/TEST-NestedPass.1.xml', expr='failures="0" name="NestedPass" skipped="0" tests="1"')
		self.assertGrep('target/pysys-reports/TEST-NestedPass.2.xml', expr='failures="0" name="NestedPass" skipped="0" tests="1"')
		self.assertGrep('target/pysys-reports/TEST-NestedTimedout.1.xml', expr='failures="1" name="NestedTimedout" skipped="0" tests="1"')
		self.assertGrep('target/pysys-reports/TEST-NestedTimedout.1.xml', expr='<failure message="TIMED OUT">Reason for timed out outcome is general tardiness</failure>')
		
		datedtestsum = glob.glob(self.output+'/testsummary-*.log')
		if len(datedtestsum) != 1: self.addOutcome(FAILED, 'Did not find testsummary-<year>.log')

		self.assertLineCount('pysys.out', expr='Summary of non passes', condition='==1')
		self.assertOrderedGrep('pysys.out', exprList=[
			'Summary of non passes: ',
			'CYCLE 1.*TIMED OUT.*NestedTimedout',
			'Reason for timed out outcome is general tardiness',
			'CYCLE 1.*FAILED.*NestedFail',
			'CYCLE 2.*TIMED OUT.*NestedTimedout',
		])
