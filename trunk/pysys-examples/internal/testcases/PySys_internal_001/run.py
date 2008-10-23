from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		os.environ["TEST_USER"] = "Felicity Kendal"
		self.proj = Project(self.input, 'pysysproject.xml'))
	
	def validate(self):
		self.assertTrue(self.proj.env_user == "Felicity Kendal")
		self.assertTrue(self.proj.env_user_prepend == "append-on-front-Felicity Kendal")
		self.assertTrue(self.proj.env_user_append == "Felicity Kendal-append-on-back")
		self.assertTrue(self.proj.env_default == "default value")
		self.assertTrue(self.proj.env_default_none == "")
		self.assertTrue(self.proj.user_firstname == "Simon")
		self.assertTrue(self.proj.user_lastname == "Smith")
		self.assertTrue(self.proj.user_title == "Professor")
		self.assertTrue(self.proj.user_full == "Professor Simon Smith")