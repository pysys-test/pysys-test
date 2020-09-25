# -*- coding: latin-1 -*-

# Part of this test: for pre-1.6.0 compatibility check this works for classes defined in subpackages
from pysys.writer import *
assert PythonCoverageWriter
assert replaceIllegalXMLCharacters
assert stripANSIEscapeCodes


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

		import coverage # this test requires the coverage.py library so give a clear error if it's missing

		self.copy(self.input, self.output+'/test')
		# make testRootDir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		runPySys(self, 'pysys', ['run', '--progress', '-o', self.output+'/myoutdir', '--record', '--cycle', '2', '-XcodeCoverage'], 
			workingDir='test', ignoreExitStatus=True, environs={
				# this is a good test in which to test the default behaviour works when enabled
				'PYSYS_CONSOLE_FAILURE_ANNOTATIONS':'',
			})
		self.logFileContents('pysys.out', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
		
		# delete code coverage files to avoid confusing parent Python process
		self.deletedir('myoutdir/__coverage_python.myoutdir')
		self.deletedir('myoutdir/NestedPass')
		
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
		self.assertThatGrep('target/pysys-reports/TEST-NestedTimedout.1.xml', '<failure .*/>', 
			expected='<failure message="TIMED OUT: Reason for timed out outcome is general tardiness - %s" type="TIMED OUT"/>'%TEST_STR, encoding='utf-8')
		# check stdout is included, and does not have any ANSI control characters in it
		self.assertThat('junitStdoutOutcome == expected', expected='TIMED OUT', 
			junitStdoutOutcome=self.getExprFromFile('target/pysys-reports/TEST-NestedTimedout.1.xml', expr='Test final outcome: *(.*)', encoding='utf-8'))
		
		datedtestsum = glob.glob(self.output+'/testsummary-*.log')
		if len(datedtestsum) != 1: self.addOutcome(FAILED, 'Did not find testsummary-<year>.log')

		# check these appear only once in log lines (i.e. starting with a digit; excludes repetitions from CI providers)
		self.assertLineCount('pysys.out', expr='[0-9].*Total test duration:', condition='==1')
		self.assertLineCount('pysys.out', expr='[0-9].*Failure outcomes: .*2 TIMED OUT, 2 FAILED', condition='==1')
		self.assertLineCount('pysys.out', expr='[0-9].*Success outcomes: .*2 PASSED', condition='==1')
		self.assertGrep('pysys.out', expr=' +[(]title: .*Nested testcase fail.*[)]')

		self.assertLineCount('pysys.out', expr='Summary of failures', condition='==1')
		self.assertOrderedGrep('pysys.out', exprList=[
			'[0-9].*Summary of failures: ',
			'[0-9].*CYCLE 1.*TIMED OUT.*NestedTimedout',
			'[0-9].*Reason for timed out outcome is general tardiness - %s'%(
				# stdout seems to get written in utf-8 not local encoding on python2 for some unknown reason, so skip verification of extra chars on that version; 
				# for python 3 we can do the full verification
				'Hello' if sys.version_info[0] == 2 else TEST_STR),
			'[0-9].*CYCLE 1.*FAILED.*NestedFail',
			'[0-9].*CYCLE 2.*TIMED OUT.*NestedTimedout',
		])
		# check the title and output dirs
		self.assertOrderedGrep('pysys.out', exprList=[
			'Summary of failures:',
			'CYCLE 1.*FAILED.*NestedFail',
			'[(]title: .*Nested testcase fail[)]',
			 'NestedFail.',
			 '.*myoutdir.NestedFail.cycle1.',
		])


		self.assertOrderedGrep('pysys.out', exprList=[
			r'Run details:',
			r'      *outDirName: [^/\\]*myoutdir',
			r'      *hostname: .+',
			])

		# check the option works to disable this
		self.assertGrep('pysys.out', expr='List of failure test ids:', contains=False)
		
		self.assertPathExists('myoutdir/__pysys_output_archives.myoutdir/NestedFail.cycle001.myoutdir.zip')
		
		# check Python code coverage worked
		self.assertGrep('pysys.out', expr='Preparing Python coverage report in: .*__coverage_python.myoutdir')
		self.assertThatGrep('pysys.out', 'Executed .*python-coverage-html.*(exit status .*)', 
			'value == expected', expected='exit status 0')

		self.assertGrep('pysys.out', expr='Published artifact TestOutputArchive: .+/NestedFail.cycle002.myoutdir.zip')
		self.assertGrep('pysys.out', expr='Published artifact TestOutputArchiveDir: .+/__pysys_output_archives.myoutdir')
		self.assertGrep('pysys.out', expr='Published artifact CSVPerformanceReport: .+/perf_.*.csv')
		self.assertGrep('pysys.out', expr='Published artifact JUnitXMLResultsDir: .+/pysys-reports')
		self.assertGrep('pysys.out', expr='Published artifact MyCustomCategory', contains=False) # due to publishArtifactCategoryIncludeRegex

		self.assertGrep('pysys.out', expr='Published artifact .*[.][.].*', contains=False)
		
		self.assertThat('len(vcsCommit) > 4', vcsCommit__eval="self.runner.runDetails['vcsCommit']")
		
		# check PYSYS_CONSOLE_FAILURE_ANNOTATIONS did its thing
		self.assertThat('actual.endswith(expected)', actual=self.getExprFromFile('pysys.out', '^[^0-9].*error: .*NestedTimedout .* 02.*', encoding=locale.getpreferredencoding()), 
			expected=u'NestedTimedout%srun.py:12: error: TIMED OUT - Reason for timed out outcome is general tardiness - %s (NestedTimedout [CYCLE 02])'%(os.sep, TEST_STR))

		self.assertThat('actual.endswith(expected)', actual=self.getExprFromFile('pysys.out', '^[^0-9].*warning: .*NestedNotVerified .* 02.*'), 
			expected='2%srun.log:0: warning: NOT VERIFIED - (no outcome reason) (NestedNotVerified [CYCLE 02])'%os.sep)
