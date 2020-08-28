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


		# Start the server application we're testing (as a background process)
		# self.project provides access to properties in pysysproject.xml, such as appHome which is the 
		# location of the application we're testing.
		if True or not IS_WINDOWS:
			server1 = self.startProcess(
				command   = sampledir+'/bin/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
				arguments = ['--port', str(self.getNextAvailableTCPPort())], 
				environs  = os.environ,#self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE)),
				stdouterr = 'my_server1', displayName = 'my_server1<port %s>', background = True,
				)
			# Wait for the server to start by polling for a grep regular expression. The errorExpr/process 
			# arguments ensure we abort with a really informative message if the server fails to start.
			try:
				self.waitForGrep('my_server1.out', '.', errorExpr=[' (ERROR|FATAL) '], process=server1, timeout=8) 
				self.waitForGrep('my_server1.out', 'Started MyServer .*on port .*', errorExpr=[' (ERROR|FATAL) '], process=server1, timeout=8) 
			except Exception as ex:
				self.log.info('Failed to start 1: %s; %s', ex, os.listdir(self.output))
				pass

			server2 = self.startProcess(
				command   = sampledir+'/bin/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
				arguments = ['--port', str(self.getNextAvailableTCPPort())], 
				environs  = os.environ,#self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE)),
				stdouterr = 'my_server2', displayName = 'my_server2<port %s>', background = False, timeout=10,
				)
			

			self.logFileContents('my_server1.out')
			self.logFileContents('my_server1.err')
			
			self.logFileContents('my_server2.out')
			self.logFileContents('my_server2.err')
			server1.stop()
			server2.stop()
		
	
		def pysys(name, args, **kwargs):
			if args[0] == 'run': args = args+['-o', self.output+'/'+name]
			runPySys(self, name, args, workingDir=sampledir+'/test', 
				**kwargs)

		runcmd = 'run --ci -vDEBUG'
		# The main test here is that the tests pass; in case it fails, log the server output
		self.addCleanupFunction(lambda: self.logFileContents('pysys-run-tests/MyServer_002/my_server1.out'))
		self.addCleanupFunction(lambda: self.logFileContents('pysys-run-tests/MyServer_002/my_server1.err'))
		try:
			pysys('pysys-run-tests', runcmd.split(' '), ignoreExitStatus=False)
		except:
			self.logFileContents('pysys-run-tests.out', maxLines=0)
			raise
		
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
