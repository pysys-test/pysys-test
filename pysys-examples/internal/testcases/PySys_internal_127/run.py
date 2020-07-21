from pysys.constants import *
from pysys.exceptions import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	
	def startTestProcess(self, **kwargs):
		try:
			return self.startPython([self.input+'/test.py']+kwargs.pop('arguments',[]), disableCoverage=True, displayName='python<%s>'%kwargs['stdouterr'], **kwargs)
		except Exception as ex: # test abort
			self.log.info('Got expected exception: %s', ex)
	
	def execute(self):
		self.logFileContentsDefaultExcludes=['Umm.*']
	
		self.startTestProcess(stdouterr='default')
		self.startTestProcess(stdouterr='default_timeout', arguments=['block'], timeout=0.1)
		self.startTestProcess(stdouterr='onError=noop', onError=lambda process: None)
		self.write_text('logfile.log', 'This is a log file')
		self.startTestProcess(stdouterr='onError=logfile', onError=lambda process: self.logFileContents('logfile.log'))
		self.startTestProcess(stdouterr='onError=stdout', onError=lambda process: self.logFileContents(process.stdout, tail=True))

		# these example are in the documentation
		self.startTestProcess(stdouterr='onError=doc_example_suffix', 
			onError=lambda process: self.logFileContents(process.stderr) and self.getExprFromFile(process.stderr, 'ERROR: (.+)'))

		self.startTestProcess(stdouterr='onError=doc_example', 
			onError=lambda process: self.logFileContents(process.stderr, tail=True) or self.logFileContents(process.stdout, tail=True))

		p = self.startTestProcess(stdouterr='background-wait', background=True, expectedExitStatus='<=0')
		try:
			self.waitProcess(p, timeout=100, checkExitStatus=True)
		except AbortExecution as ex:
			self.log.info('Got expected exception: %s'%ex)
		else:
			assert False, 'Should have got exception from waitProcess'
		self.waitProcess(p, timeout=100) # default should not give an exception
		
		self.addOutcome(PASSED, override=True)
		def m(line):
			if 'Contents of default_timeout.err' in line: return None # race condition whether this gets created in time
			if 'Executed' in line:	return '\n'+line[line.find('<'):]
			if 'timed out' in line: return '\nTimed out process\n'
			if 'Contents' in line: return line[line.find('Contents'):]
			if 'Got expected exception' in line: return line[line.find('Got '):]
			return None
		self.copy('run.log', 'output.txt', mappers=[m])
		

	def validate(self):
		self.assertDiff('output.txt')
		self.assertGrep('run.log', expr='Ummmmm', contains=False)