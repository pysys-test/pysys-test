from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	
	def startTestProcess(self, **kwargs):
		try:
			self.startPython([self.input+'/test.py']+kwargs.pop('arguments',[]), **kwargs)
		except Exception as ex: # test abort
			self.log.info('Suppressing exception: %s', ex)
	
	def execute(self):
		self.startTestProcess(stdouterr='default')
		self.startTestProcess(stdouterr='default_timeout', arguments=['block'], timeout=0.1)
		self.startTestProcess(stdouterr='onError=noop', onError=lambda process: None)
		self.write_text('logfile.log', 'This is a log file')
		self.startTestProcess(stdouterr='onError=logfile', onError=lambda process: self.logFileContents('logfile.log'))
		self.startTestProcess(stdouterr='onError=stdout', onError=lambda process: self.logFileContents(process.stdout, tail=True))
		
		# this example is the documentation
		self.startTestProcess(stdouterr='onError=doc_example', 
			onError=lambda process: self.logFileContents(process.stderr, tail=True) or self.logFileContents(process.stdout, tail=True))

		self.addOutcome(NOTVERIFIED, override=True)
		def m(line):
			if 'Suppressing' in line: return None
			if 'Executed' in line:	return '\n'+line[line.find('<'):]
			if 'timed out' in line: return '\nTimed out process\n'
			if 'Contents' in line: return line[line.find('Contents'):]
			return None
		self.copy('run.log', 'output.txt', mappers=[m])
		

	def validate(self):
		self.assertDiff('output.txt')
