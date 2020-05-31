# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob, locale

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		if locale.getpreferredencoding() in ['ANSI_X3.4-1968', 'ascii']: self.skipTest('cannot run in ASCII locale')

		self.copy(self.input, self.output+'/test')
		# make testRootDir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		runPySys(self, 'pysys', ['run', '--progress', '-o', self.output+'/myoutdir', '--record', '--cycle', '2'], workingDir='test', ignoreExitStatus=True)
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)
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

		# nb: the order of attributes can vary across python releases e.g. 3.7->3.8, so compare the parsed XML
		import xml.etree.ElementTree as ET
		self.assertEval("{xml_NestedPass1} == {expected}", 
			xml_NestedPass1="name={name}, tests={tests}, failures={failures}, skipped={skipped}".format(**dict(ET.parse(self.output+'/target/pysys-reports/TEST-NestedPass.1.xml').getroot().attrib)),
			expected='name=NestedPass, tests=1, failures=0, skipped=0')
		self.assertGrep('target/pysys-reports/TEST-NestedPass.1.xml', expr='<testsuite .* time="[0-9.]+"', encoding='utf-8')

		self.assertEval("{xml_NestedPass1} == {expected}", 
			xml_NestedPass1="name={name}, tests={tests}, failures={failures}, skipped={skipped}".format(**dict(ET.parse(self.output+'/target/pysys-reports/TEST-NestedPass.2.xml').getroot().attrib)),
			expected='name=NestedPass, tests=1, failures=0, skipped=0')

		self.assertEval("{xml_NestedTimedout1} == {expected}", 
			xml_NestedTimedout1="name={name}, tests={tests}, failures={failures}, skipped={skipped}".format(**dict(ET.parse(self.output+'/target/pysys-reports/TEST-NestedTimedout.2.xml').getroot().attrib)),
			expected='name=NestedTimedout, tests=1, failures=1, skipped=0')
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
		# check the option works to disable this
		self.assertGrep('pysys.out', expr='List of non passing test ids:', contains=False)