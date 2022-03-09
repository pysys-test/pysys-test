from pysys.constants import *
from pysys.exceptions import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	
	def startTestProcess(self, **kwargs):
		try:
			return self.startPython([self.input+'/test.py']+kwargs.pop('arguments',[]), disableCoverage=True, displayName='python<%s>'%kwargs['stdouterr'], **kwargs)
		except Exception as ex: # test abort
			self.log.info('Suppressing exception: %s', ex)
	
	def execute(self):
		self.logFileContentsDefaultExcludes=['Umm.*']

		block = self.startTestProcess(stdouterr='timeout', arguments=['block'], background=True)
		self.waitForBackgroundProcesses(excludes=[block])
		block.stop()
		del self.processList[:]

		self.startTestProcess(stdouterr='failure1', background=True)
		self.waitForBackgroundProcesses(checkExitStatus=True, abortOnError=False)  # should fail

		p1 = self.startTestProcess(stdouterr='failure2', background=True)
		p2 = self.startTestProcess(stdouterr='failure-expected', expectedExitStatus='!=0', background=True)
		
		# avoid race by manually waiting for these two to ensure a consistent state before we test waitForBackgroundProcesses
		p1.wait(60)
		p2.wait(60)
		
		self.waitForBackgroundProcesses(checkExitStatus=False) # should succeed
		self.waitForBackgroundProcesses(abortOnError=False) # should fail
		self.waitForBackgroundProcesses([p1, p2], abortOnError=False) # should fail
		
		
		self.startTestProcess(stdouterr='timeout1', arguments=['block'], background=True)
		self.startTestProcess(stdouterr='timeout2', arguments=['block'], background=True)
		self.waitForBackgroundProcesses(timeout=0.1, abortOnError=False, checkExitStatus=True)  # should fail

		self.addOutcome(PASSED, override=True)
		def m(line):
			line = re.sub('[0-9.]+ secs', 'N secs', line)
			if ' WARN ' in line: 
				line = line[line.find(' WARN ')+1:]
			elif ' INFO ' in line: 
				line = line[line.find(' INFO ')+1:]

			if 'Waiting ' in line: return line
			if 'Contents' in line: return line[line.find('Contents'):]
			if ' WARN ' in line: return line
			if 'exit status' in line: return line
			if 'failed' in line: return line
			if 'timed out' in line: return line
			
			return None
		self.copy('run.log', 'output.txt', mappers=[m])


	def validate(self):
		self.assertDiff('output.txt')
