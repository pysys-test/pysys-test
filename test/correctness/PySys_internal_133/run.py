import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.assertThat('actual == expected', actual=pysys.utils.fileutils.loadJSON(self.input+'/test.json'), expected={
			'PoundSign':[u'\xa3'],
			'Number': [123, 456.789]
		})

		self.write_text('tobedeleted.txt', 'foo bar')
		self.deleteFile('tobedeleted.txt', ignore_errors=True)
		self.assertPathExists('tobedeleted.txt', exists=False)
		self.deleteFile('tobedeleted.txt')
		
	def validate(self):
		pass