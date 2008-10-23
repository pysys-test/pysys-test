from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		os.environ["TEST_USER"] = "Felicity Kendal"
		self.proj = Project(self.input, 'pysysproject.xml')
		for attr in dir(self.proj):
			if attr in ['lib', 'library', 'version', 'user']:
				self.log.info("%s = %s", attr, eval("self.proj.%s" % attr))
			
	def validate(self):
		self.assertTrue(self.proj.lib == 'lib_%s_1.0.so'%OSFAMILY)
		self.assertTrue(self.proj.library == 'jstore1.0.jar')
		self.assertTrue(self.proj.version == '1.0')
		
		
		