import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import PY2

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		if PY2: self.skipTest('Samples work on Python 3 only')
		
		sampledir = self.project.testRootDir+'/../samples/getting-started'
	
		def pysys(name, args, **kwargs):
			if args[0] == 'run': args = args+['-o', self.output+'/'+name]
			runPySys(self, name, args, workingDir=sampledir+'/test', 
				**kwargs)

		runcmd = 'run --ci'
		# The main test here is that the tests pass
		pysys('pysys-run-tests', runcmd.split(' '), ignoreExitStatus=False)
		
		pysys('pysys-print', ['print'], background=True)
		self.waitForBackgroundProcesses()


	def validate(self):	
		outdir = self.output+'/pysys-run-tests'
		
		# Check we generated the expected output files from all our writers, code coverage, etc
		self.write_text('outdir-contents.txt', '\n'.join(sorted([re.sub('[0-9]', 'N', f)+(
				'/' if (os.path.isdir(outdir+os.sep+f) and os.listdir(outdir+os.sep+f)) else '') # make sure we notice if any dirs are empty
			for f in os.listdir(outdir) 
			if os.path.isfile(f) or f.startswith('_')])))
		self.assertDiff('outdir-contents.txt')

		# Server build number in runDetails
		self.assertGrep('pysys-run-tests.out', 'myServerBuildNumber: .+')

		self.logFileContents('pysys-run-tests.out', tail=True)
		self.logFileContents('pysys-print.out', tail=True, maxLines=0)