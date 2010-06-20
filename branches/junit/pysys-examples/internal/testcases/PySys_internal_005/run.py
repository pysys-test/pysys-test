from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		self.proj = Project(self.input, 'pysysproject.xml')
	
	def validate(self):
		self.assertTrue(self.proj.loc == self.input)
