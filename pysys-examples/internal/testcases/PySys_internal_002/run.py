from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		self.proj = Project(self.input)
		self.log.info(self.proj.version)
		self.log.info(self.proj.library)
		self.log.info(self.proj.lib)
			
	def validate(self):
		pass