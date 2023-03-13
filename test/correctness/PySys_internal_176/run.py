import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		if sys.version_info[0:2] < tuple([3,6]): self.skipTest('Samples work on Python 3.6+ only')

		sampledir = self.project.testRootDir+'/../samples/cookbook'

		self.pysys.pysys('pysys-print', ['print'], workingDir=sampledir+'/test', background=True)
		self.pysys.pysys('pysys-print-descriptor-samples', ['print', '--full', 'PySysDirConfigSample', 'PySysTestXMLDescriptorSample', 'PySysTestPythonDescriptorSample'], workingDir=sampledir+'/test', background=True)
		self.pysys.pysys('pysys-print-descriptor-samples-json', ['print', '--json', 'PySysDirConfigSample', 'PySysTestXMLDescriptorSample', 'PySysTestPythonDescriptorSample'], workingDir=sampledir+'/test', background=True)
		self.pysys.pysys('pysys-run-help', ['run', '-h'], workingDir=sampledir+'/test', background=True)

		self.pysys.pysys('make-help', ['make', '-h'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample', background=True)
		self.pysys.pysys('make-default', ['make', self.output+'/NewTest_Default'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample', background=True)
		self.pysys.pysys('make-existing-foobar', ['make', '--template=foobar-test', self.output+'/NewTest_ExistingTest'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample', background=True)
		self.pysys.pysys('make-perf-test', ['make', '--template=perf-test', self.output+'/NewTest_PerfTest'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample', background=True)
		self.pysys.pysys('make-pysys-xml-test', ['make', '--template=pysys-xml-test', self.output+'/NewTest_XML'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample', background=True)
		self.waitForBackgroundProcesses()

	def validate(self):	
		# Sample descriptors
		self.assertDiff(self.copy('pysys-print-descriptor-samples.out', 'descriptor-samples.txt', mappers=[
			lambda line: line.replace(os.sep, '/'),
			pysys.mappers.RegexReplace(' [^ ]+pysys-extensions', ' <rootdir>/pysys-extensions')]))
		
		# Test making
		self.assertDiff(self.write_text('NewTest_Default-files.txt', '\n'.join(pysys.utils.fileutils.listDirContents(self.output+'/NewTest_Default'))))
		self.assertDiff(self.write_text('NewTest_ExistingTest-files.txt', '\n'.join(pysys.utils.fileutils.listDirContents(self.output+'/NewTest_ExistingTest'))))
		# this shows we replaced the user of the original committed test (mememe) with the "current" user
		self.assertThatGrep('NewTest_ExistingTest/pysystest.py', '__pysys_authors__ *= "([^"]+)"', expected='pysystestuser')
		self.assertThatGrep('NewTest_ExistingTest/pysystest.py', '__pysys_created__ *= "([^"]+)"', 'value != "1999-12-31"')

		self.assertThatGrep('NewTest_PerfTest/pysystest.py', '(.*)pass', expected=2*4*' ') # converted spaces to tabs

		# check that the new test got our standard descriptor
		self.assertThatGrep('NewTest_Default/pysystest.py', '     +(---+)$', 'len(value) == expected', expected=120) # customized with project property

		# check the legacy one works ok too
		self.assertThatGrep('NewTest_XML/pysystest.xml', 'created="([^"]+)"', 're.match(expected, value)', expected=r'\d\d\d\d-\d\d-\d\d')
		self.assertGrep('NewTest_XML/run.py', 'PySysTest')
		
		self.logFileContents('pysys-run-help.out', tail=True)
		self.logFileContents('pysys-run-tests.out', tail=False)	
		self.logFileContents('pysys-run-tests.out', tail=True, maxLines=50)
		self.logFileContents('pysys-print.out', tail=True, maxLines=0)

		self.logFileContents('make-help.out', tail=True, maxLines=0)
