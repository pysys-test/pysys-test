from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		self.proj = Project(self.input, 'pysysproject.xml')
		stdoutHandler.setFormatter(self.project.formatters.stdout)
		
	def validate(self):
		self.assertTrue(self.proj.loc == self.input)
