from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.mkdir('dir1/dir1a') # nothing in it

		with open(self.mkdir(self.output+'/dir2/dir2a/')+'/empty.txt', 'w') as f: # something in it but will be deleted as empty
			pass

		with open(self.output+'/nonempty.txt', 'w') as f:
			f.write('something')
		with open(self.output+'/empty.txt', 'w') as f:
			pass

		self.addOutcome(INSPECT, 'inspect')
	def validate(self):
		pass 
