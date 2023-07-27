import glob
import json
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

		def pysys(name, args, **kwargs):
			if args[0] == 'run': args = args+['-o', self.output+'/'+name]
			runPySys(self, name, args, workingDir=sampledir+'/test', 
				# this is so we can run git
				environs={'PATH':os.environ['PATH']}, 
				disableCoverage=True, # the COVERAGE_FILE setting from the top-level run stops the coverage gen within the cookbook pysys going to the right place so disable
				**kwargs)

		# The command below is copied verbatim from the README.md
		runcmd = 'run -j0 --record -XcodeCoverage --exclude=manual'
		self.assertGrep(sampledir+'/README.md', runcmd)
		self.log.info('Running the cookbook sample: pysys %s'%runcmd)
		pysys('pysys-run-tests', runcmd.split(' '), ignoreExitStatus=True)
		
		# delete sample coverage files so we don't pick them up and use them for PySys itself
		for root, dirs, files in os.walk(self.output):
			for f in files:
				if '.coverage' in f:
					os.remove(root+os.sep+f)

	def validate(self):	
		outdir = self.output+'/pysys-run-tests'
		
		self.assertGrep('pysys-run-tests.err', 'ERROR', contains=False) # for FATAL ERRORs

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

		if self.assertThat('len(performanceFiles)==2 and ".json" in "".join(performanceFiles)', performanceFiles=glob.glob(outdir+'/__pysys_performance/*/*')):
			# check it's valid json
			with open(glob.glob(outdir+'/__pysys_performance/*/*.json')[0]) as f:
				json.load(f)
		
		# Check the code coverage include filter worked
		self.assertGrep(outdir+'/__coverage_python.pysys-run-tests/python-coverage-combine.out', 'PyUnitTest')
		self.assertGrep(outdir+'/__coverage_python.pysys-run-tests/python-coverage-combine.out', 'Outcome_FailedAssertions')
		self.assertGrep(outdir+'/__coverage_python_unit_tests.pysys-run-tests/python-coverage-combine.out', 'PyUnitTest')
		self.assertGrep(outdir+'/__coverage_python_unit_tests.pysys-run-tests/python-coverage-combine.out', 'Outcome_FailedAssertions', contains=False)
