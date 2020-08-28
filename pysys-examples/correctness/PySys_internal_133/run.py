import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.assertThat('actual == expected', actual=pysys.utils.fileutils.loadJSON(self.input+'/test.json'), expected={
			'PoundSign':[u'\xa3'],
			'Number': [123, 456.789]
		})

		
	def validate(self):
		pass