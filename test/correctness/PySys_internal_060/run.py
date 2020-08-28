from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		with open(self.output+'/test.txt', 'w') as f:
			f.write('\n'.join(['abc', 'abde', 'x', 'x', 'abe', 'abx']))

	def validate(self):
		self.assertLineCount('test.txt', expr='b', ignores=['x', '[dD]'], condition='==2')