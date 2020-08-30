import os, sys, math, shutil
from pysys.constants import *
from pysys.basetest import BaseTest

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-output', '-v', 'debug'], workingDir='test', ignoreExitStatus=True)
		self.logFileContents('pysys.out', maxLines=0)

		# quick interactive demo of success
		def mythreadtarget(log, stopping):
			log.info('Hello from thread!')
			while not stopping.is_set():
				if not stopping.wait(1): return
		t = self.startBackgroundThread('MyBackgroundThread', mythreadtarget)
		t.stop().join()
			
	def validate(self):
	
		# ensure output from thread makes it into both stdout and run.log
		for f in ['pysys-output/Success/run.log', 'pysys.out']:
			self.assertGrep(f, expr=r'DEBUG .*\[Success.FunctionThread\] starting')
			self.assertGrep(f, expr=r'DEBUG .*\[Success.FunctionThread\] completed successfully')

			self.assertGrep(f, expr=r'INFO .*Hello from function thread')
			# checks parameter passing
			self.assertGrep(f, expr=r'INFO .*Hello from instance method thread: param=123')
	
		self.assertOrderedGrep('pysys-output/Success/run.log', exprList=[
		'End of execute',
		'Joining background thread .*FunctionThread',
		'cleanup function done',
		])
		self.assertGrep('pysys-output/Success/run.log', expr=r'Test final outcome:.*PASSED')
		self.log.info('')
		
		self.assertGrep('pysys-output/JoinCleanupException/run.log', expr=r'ERROR .*Background thread FunctionThread failed')
		self.assertOrderedGrep('pysys-output/JoinCleanupException/run.log', exprList=[
			r'Traceback \(most recent call last\)', 
			r'Exception: Simulated exception from background thread',
			r'End of execute',
			])
		self.assertGrep('pysys-output/JoinCleanupException/run.log', expr=r'Test final outcome:.*BLOCKED')
		self.assertGrep('pysys-output/JoinCleanupException/run.log', expr=r'Test outcome reason:.*Background thread FunctionThread failed with Exception: Simulated exception from background thread')
		self.log.info('')
		
		self.assertOrderedGrep('pysys-output/JoinExecuteException/run.log', exprList=[
			r'ERROR .*Background thread FunctionThread failed',
			r'Traceback \(most recent call last\)', 
			r'Exception: Simulated exception from background thread',
			])
		self.assertGrep('pysys-output/JoinExecuteException/run.log', expr=r'End of execute', contains=False) # since we aborted on error

		self.assertGrep('pysys-output/JoinExecuteException/run.log', expr=r'Test final outcome:.*BLOCKED')
		self.assertGrep('pysys-output/JoinExecuteException/run.log', expr=r'Test outcome reason:.*Background thread FunctionThread failed with Exception: Simulated exception from background thread')
		self.log.info('')

		self.assertOrderedGrep('pysys-output/JoinCleanupTimeout/run.log', exprList=[
			r'--- test cleanup',
			r'DEBUG .*Stop.* requested for background thread FunctionThread',
			r'INFO .*Joining .*FunctionThread',
			r'WARN .*FunctionThread.* is still running after waiting for allocated timeout period \(\d secs\) ... .*timed out',
			r'WARN .*Stack of hanging thread FunctionThread:',
			'functionThatAppearsToHang',
			])
		self.assertGrep('pysys-output/JoinCleanupTimeout/run.log', expr=r'Test final outcome:.*TIMED OUT')
		self.assertGrep('pysys-output/JoinCleanupTimeout/run.log', expr=r'Test outcome reason:.*Background thread FunctionThread is still running after waiting for allocated timeout period')
		self.log.info('')

		self.assertOrderedGrep('pysys-output/JoinExecuteTimeout/run.log', exprList=[
			r'INFO .*Joining background thread .*FunctionThread',
			r'WARN .*Background thread FunctionThread is still running after waiting for allocated timeout period \(\d secs\) ... .*timed out',
			r'End of execute', 
			])
		self.assertGrep('pysys-output/JoinExecuteTimeout/run.log', expr=r'Test final outcome:.*TIMED OUT')
		self.assertGrep('pysys-output/JoinExecuteTimeout/run.log', expr=r'Test outcome reason:.*Background thread FunctionThread is still running after waiting for allocated timeout period')
		self.log.info('')

		# check we don't have any errors as a result of writing output from background thread 
		# after run.log stream has been closed
		self.logFileContents('pysys.err')
		self.assertGrep('pysys.err', expr='Traceback.*', contains=False)
		