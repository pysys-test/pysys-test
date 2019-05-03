from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.mkdir('dir1/dir1a')

		with open(self.mkdir(self.output+'/dir2/dir2a/')+'/nonempty.txt', 'w') as f:
			f.write('something')

		with open(self.output+'/nonempty.txt', 'w') as f:
			f.write('something')
		with open(self.output+'/empty.txt', 'w') as f:
			pass

	def validate(self):
		pass 
