from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.utils.pycompat import PY2

class PySysTest(BaseTest):
	testBooleanProperty = False
	testIntProperty = 123
	testFloatProperty = 456.7
	testStringProperty = '12345'
	testNoneProperty = None
	testFloatUserData = 0.0

	def execute(self):
		self.proj = self.project
		self.assertTrue(self.proj.env_user == "Felicity Kendal")
		self.assertTrue(self.proj.env_user_prepend == "append-on-front-Felicity Kendal")
		self.assertTrue(self.proj.env_user_append == "Felicity Kendal-append-on-back")
		self.assertTrue(self.proj.env_default == "default value")
		self.assertTrue(self.proj.env_default_none == "")
		self.assertTrue(self.proj.user_firstname == "Simon")
		self.assertTrue(self.proj.user_lastname == "Smith")
		self.assertTrue(self.proj.user_title == "Professor")
		self.assertTrue(self.proj.user_full == "Professor Simon Smith")

		for p in ['projectbool', 'projectbooloverride', 'cmdlineoverride']:
			self.log.info('getBoolProperty %s=%r', p, self.getBoolProperty(p))
		
		# no type coersion if not defined as a basetest property
		self.assertEval('{cmdlineoverride} == "tRue"', cmdlineoverride=self.cmdlineoverride)

		self.log.info('getBoolProperty %s=%r', 'booldeftrue', self.getBoolProperty('bool-not-defined', True))
		self.log.info('getBoolProperty %s=%r', 'booldeffalse', self.getBoolProperty('bool-not-defined', False))		

		# check type coersion based on base test type
		self.assertThat('testBooleanProperty is True', testBooleanProperty=self.testBooleanProperty)
		self.assertThat('testIntProperty == 1234', testIntProperty=self.testIntProperty)
		self.assertThat('testFloatProperty == 456.78', testFloatProperty=self.testFloatProperty)
		self.assertThat('testStringProperty == "123456"', testStringProperty=self.testStringProperty)
		self.assertThat('testNoneProperty == "Hello"', testNoneProperty=self.testNoneProperty)
		self.assertThat('testStringUserData == expected', testStringUserData=self.testStringUserData, expected='Hello ${non-existent}')


	def validate(self):
		pass 
