from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

class PySysTest(BaseTest):

	def execute(self):
		self.proj = Project(self.input, 'pysysproject.xml')
		for attr in dir(self.proj):
			if attr in ['lib', 'library', 'version', 'user']:
				self.log.info("%s = %s", attr, eval("self.proj.%s" % attr))
		stdoutHandler.setFormatter(PROJECT.formatters.stdout)
		
		# good opportunity to check that default project props are set
		self.assertThat('%s != ""', repr(self.proj.os)) # renamed from osfamily by config
		self.assertThat('%s != ""', repr(self.proj.root))
		self.assertThat('%s != ""', repr(self.proj.hostname))
		self.assertThat('re.match(r"\d\d\d\d-\d\d-\d\d$", %s)', repr(self.proj.startDate))
		self.assertThat('re.match(r"\d\d\.\d\d\.\d\d$", %s)', repr(self.proj.startTime))
		
	def validate(self):
		self.assertTrue(self.proj.lib == 'lib_%s_1.0.so'%OSFAMILY)
		self.assertTrue(self.proj.library == 'jstore1.0.jar')
		self.assertTrue(self.proj.version == '1.0')
		
		
		