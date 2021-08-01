import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import PY2

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		if sys.version_info[0:2] < tuple([3,6]): self.skipTest('Samples work on Python 3.6+ only')

		sampledir = self.project.testRootDir+'/../samples/cookbook'

		def pysys(name, args, **kwargs):
			if args[0] == 'run': args = args+['-o', self.output+'/'+name]
			runPySys(self, name, args, workingDir=sampledir+'/test', 
				# this is so we can run git
				environs={'PATH':os.environ['PATH']}, 
				**kwargs)

		# The command below is copied verbatim from the README.md
		runcmd = 'run -j0 --record -XcodeCoverage --exclude=manual'
		self.assertGrep(sampledir+'/README.md', runcmd)
		pysys('pysys-run-tests', runcmd.split(' '), ignoreExitStatus=True)
		
		pysys('pysys-print', ['print'], background=True)
		pysys('pysys-print-descriptor-samples', ['print', '--full', 'PySysDirConfigSample', 'PySysTestXMLDescriptorSample', 'PySysTestPythonDescriptorSample'], background=True)
		pysys('pysys-print-descriptor-samples-json', ['print', '--json', 'PySysDirConfigSample', 'PySysTestXMLDescriptorSample', 'PySysTestPythonDescriptorSample'], background=True)
		pysys('pysys-run-help', ['run', '-h'], background=True)
		self.waitForBackgroundProcesses()
		
		# delete sample coverage files so we don't pick them up and use them for PySys itself
		for root, dirs, files in os.walk(self.output):
			for f in files:
				if '.coverage' in f:
					os.remove(root+os.sep+f)

		self.pysys.pysys('make-help', ['make', '-h'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample')
		self.pysys.pysys('make-default', ['make', self.output+'/NewTest_Default'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample')
		self.pysys.pysys('make-existing-foobar', ['make', '--template=foobar-test', self.output+'/NewTest_ExistingTest'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample')
		self.pysys.pysys('make-perf-test', ['make', '--template=perf-test', self.output+'/NewTest_PerfTest'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample')
		self.pysys.pysys('make-pysys-xml-test', ['make', '--template=pysys-xml-test', self.output+'/NewTest_XML'], workingDir=sampledir+'/test/demo-tests/pysysdirconfig_sample')

	def validate(self):	
		outdir = self.output+'/pysys-run-tests'
		
		# Check we got the expected outcomes and outcome reasons
		self.write_text('non-passes.txt', '\n'.join(sorted(["{r[testId]} = {r[outcome]}: {r[outcomeReason]}".format(r=r) for r in
			pysys.utils.fileutils.loadJSON(outdir+'/__pysys_myresults.pysys-run-tests.json')['results']
			if r['outcome'] != 'PASSED'])))
		self.assertDiff('non-passes.txt')

		# Check we generated the expected output files from all our writers, code coverage, etc
		self.write_text('outdir-contents.txt', '\n'.join(sorted([re.sub('[0-9]', 'N', f)+(
				'/' if (os.path.isdir(outdir+os.sep+f) and os.listdir(outdir+os.sep+f)) else '') # make sure we notice if any dirs are empty
			for f in os.listdir(outdir) 
			if os.path.isfile(f) or f.startswith('_')])))
		self.assertDiff('outdir-contents.txt')

		# Git commit in runDetails
		self.assertGrep('pysys-run-tests.out', 'vcsCommit: .+')

		# Test plugin
		self.assertGrep('pysys-run-tests.out', 'MyTestPlugin.setup called; myPluginProperty=999')

		# Runner plugin
		self.assertGrep('pysys-run-tests.out', 'myPythonVersion: .+')
		self.assertGrep('pysys-run-tests.out', 'MyRunnerPlugin.setup called; myPluginProperty=True and myArg=123')
		self.assertGrep('pysys-run-tests.out', 'MyRunnerPlugin cleanup called')

		# Custom runner
		self.assertGrep('pysys-run-tests.out', 'MyRunner.setup was called; myRunnerArg=12345')
		self.assertGrep('pysys-run-tests.out', 'MyRunner.cleanup was called')

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
		self.assertThatGrep('NewTest_Default/pysystest.py', '__pysys_authors__ *= "([^"]+)"', expected='pysystestuser')
		self.assertThatGrep('NewTest_Default/pysystest.py', '     +(#+)$', 'len(value) == expected', expected=80) # customized with project property

		# check the legacy one works ok too
		self.assertThatGrep('NewTest_XML/pysystest.xml', 'authors="([^"]+)"', expected='pysystestuser')
		self.assertThatGrep('NewTest_XML/pysystest.xml', 'created="([^"]+)"', 're.match(expected, value)', expected=r'\d\d\d\d-\d\d-\d\d')
		self.assertGrep('NewTest_XML/run.py', 'PySysTest')
		
		self.logFileContents('pysys-run-help.out', tail=True)
		self.logFileContents('pysys-run-tests.out', tail=False)	
		self.logFileContents('pysys-run-tests.out', tail=True, maxLines=50)
		self.logFileContents('pysys-print.out', tail=True, maxLines=0)

		self.logFileContents('make-help.out', tail=True, maxLines=0)
