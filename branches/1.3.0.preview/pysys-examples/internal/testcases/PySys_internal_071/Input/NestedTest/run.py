from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(PASSED) # pass by default
		p = self.startProcess(command=sys.executable,
			arguments = [self.input+'/fail.py'],
			environs = dict(os.environ), 
			stdout = 'fail.out', stderr='fail.err', displayName='python failer', 
			state=FOREGROUND)

	def validate(self):
		pass 
