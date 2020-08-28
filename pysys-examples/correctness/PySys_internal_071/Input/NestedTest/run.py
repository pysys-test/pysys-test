from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED) # pass by default
		
		p = self.startProcess(command=sys.executable,
			arguments = [self.input+'/fail.py'],
			environs = dict(os.environ), 
			stdouterr = 'fail-quiet', displayName='python-failer-quiet', 
			state=FOREGROUND, ignoreExitStatus=True, quiet=True)
		
		p = self.startProcess(command=sys.executable,
			arguments = [self.input+'/fail.py'],
			environs = dict(os.environ), 
			stdouterr = 'fail1', displayName='python-failer-1', 
			expectedExitStatus='==100',
			state=FOREGROUND, abortOnError=True)
		
		p = self.startProcess(command=sys.executable,
			arguments = [self.input+'/fail.py'],
			environs = dict(os.environ), 
			stdouterr = 'fail2', displayName='python-failer-2', 
			expectedExitStatus='==123',
			state=FOREGROUND, abortOnError=False)
		
		p = self.startProcess(command=sys.executable,
			arguments = [self.input+'/fail.py'],
			environs = dict(os.environ), 
			stdouterr = 'fail3', displayName='python-failer-3', 
			state=FOREGROUND)

	def validate(self):
		pass 
