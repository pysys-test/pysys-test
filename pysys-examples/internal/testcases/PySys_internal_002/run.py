from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 
from pysys.exceptions import UserError

class PySysTest(BaseTest):

	def execute(self):
		self.proj = Project(self.input, 'pysysproject.xml')
		for attr in dir(self.proj):
			if attr in ['lib', 'library', 'version', 'user']:
				self.log.info("%s = %s", attr, eval("self.proj.%s" % attr))
		
		# good opportunity to check that default project props are set
		self.assertThat('%s != ""', repr(self.proj.os)) # renamed from osfamily by config
		self.assertThat('%s != ""', repr(self.proj.root))
		self.assertThat('%s != ""', repr(self.proj.hostname))
		self.assertThat('re.match(r"\d\d\d\d-\d\d-\d\d$", %s)', repr(self.proj.startDate))
		self.assertThat('re.match(r"\d\d\.\d\d\.\d\d$", %s)', repr(self.proj.startTime))
		self.assertThat('re.match(r"[\d.]+$", startTimeSecs)', startTimeSecs=self.proj.startTimeSecs)
		
		for k,v in self.proj.properties.items():
			self.log.info('%r = %r'%(k, v))
		
		self.assertThat('actual == expected', actual__eval="self.proj.properties['test-key']", expected="test value")
		self.assertThat('actual == expected', actual__eval="self.proj.properties['test-key_3']", expected="value  3 test value")
		self.assertThat('actual == expected', actual__eval="self.proj.properties['test-key_2']", expected="test value = awesome")

		try:
			Project(self.input, 'project-missingprops.xml')
		except UserError as e:
			self.assertThat('re.match(expected, errorMessage)', errorMessage=str(e), 
				expected=r"Cannot find properties file referenced in .+project-missingprops.xml: \".+missing.properties")
		else:
			self.addOutcome(FAILED, 'project-missingprops.xml should produce an exception')
			
		try:
			Project(self.input, 'project-missingprop.xml')
		except UserError as e:
			self.assertThat('re.match(expected, errorMessage)', errorMessage=str(e), 			
				expected=r"Cannot find path referenced in project property \"myprop\": \".+missing.txt\"")
		else:
			self.addOutcome(FAILED, 'project-missingprop.xml should produce an exception')

		try:
			Project(self.input, 'project-missingpropempty.xml')
		except UserError as e:
			self.assertThat('re.match(expected, errorMessage)', errorMessage=str(e), 
				expected=r"Cannot find path referenced in project property \"myprop\": \"\"")
		else:
			self.addOutcome(FAILED, 'project-missingpropempty.xml should produce an exception')


	def validate(self):
		self.assertTrue(self.proj.lib == 'lib_%s_1.0.so'%OSFAMILY)
		self.assertTrue(self.proj.library == 'jstore1.0.jar')
		self.assertTrue(self.proj.version == '1.0')
		self.assertThat('expected == actual', actual__eval="self.proj.myprop", expected="prop1prop2YY")
		self.assertThat('expected == actual', actual__eval="self.proj.user", expected="default_value")
		
		