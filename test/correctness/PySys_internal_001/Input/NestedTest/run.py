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
	testListProperty = []
	testMultiLineListUserData = []

	def execute(self):
		self.write_text(self.project.sample_path+'.txt', 'xxx') # check these don't contain any non-file system characters
	
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
		
		# type coersion always happens for booleans even if not defined as a basetest property
		self.assertThat('cmdlineoverride is True', cmdlineoverride=self.cmdlineoverride)

		self.log.info('getBoolProperty %s=%r', 'booldeftrue', self.getBoolProperty('bool-not-defined', True))
		self.log.info('getBoolProperty %s=%r', 'booldeffalse', self.getBoolProperty('bool-not-defined', False))		

		# check type coersion based on base test type
		self.assertThat('testBooleanProperty is True', testBooleanProperty=self.testBooleanProperty)
		self.assertThat('testIntProperty == 1234', testIntProperty=self.testIntProperty)
		self.assertThat('testFloatProperty == 456.78', testFloatProperty=self.testFloatProperty)
		self.assertThat('testStringProperty == "123456"', testStringProperty=self.testStringProperty)
		self.assertThat('testNoneProperty == "Hello"', testNoneProperty=self.testNoneProperty)
		self.assertThat('testStringUserData == expected', testStringUserData=self.testStringUserData, expected='Hello Simon')
		self.assertThat('testListProperty == expected', testListProperty=self.testListProperty, expected=['abc','def','g'])

		# check coersion based on default value supplied
		self.assertThat('projectbool is True', projectbool__eval="self.project.getProperty('projectbool', False)")
		self.assertThat('projectint == 1234', projectint__eval="self.project.getProperty('projectint', -1)")
		self.assertThat('projectfloat == 456.78', projectfloat__eval="self.project.getProperty('projectfloat', 0.0)")
		self.assertThat('projectlist == expected', projectlist__eval="self.project.getProperty('projectlist', [])", expected=['abc','def','g'])
		self.assertThat('user_lastname == "Smith"', user_lastname__eval="self.project.getProperty('user_lastname', 'xxx')")
		
		self.assertThat('actual == expected', actual=sorted([k for k in self.project.properties if k.startswith('prefix')]), 
			expected=sorted(['prefix_a', 'prefix_a5']))

		self.log.info('multiline_text:\n%s', self.project.multiline_text)
		self.assertThat('multiline_text == expected', multiline_text=self.project.multiline_text, 
			expected='First line\n\t\tsecond line\n\t\t\n\n\t\t\tthird line\n\t\t\t\n\n\t\tfourth line\n\t')
		self.log.info('multiline_cdata:\n%s', self.project.multiline_cdata)
		self.assertThat('multiline_cdata == expected', multiline_cdata=self.project.multiline_cdata, 
			expected="\n\t\tmy data >' foo\n\t\t\tbar\n\t\t\t<!-- comment -->\n\t\t\tbaz\n\t\t\nno indent\n\t\t\t\n\t\tthird line\n\t")
		self.assertThat('testMultiLineListUserData == expected', testMultiLineListUserData=self.testMultiLineListUserData, expected=[
			'First line', 'second line', 'third', 'comma-separated', 'line', 'fourth line'
		])
		
		self.assertThat('testSlashes == expected', testSlashes=self.project.testSlashes, 
			expected='mydir%smyfile'%os.sep)

		self.assertThat('testEval == expected', testEval=self.project.testEval, 
			expected='Foo foo is what Simon says test')
		self.assertThat('testEvalUserData == expected', testEvalUserData=self.testEvalUserData, 
			expected='Foo foo is what Simon says test')
			
		#self.assertThat('throws1', testStringProperty__eval="self.project.getProperty('projectfloat', -1)")
		#self.assertThat('throws2', testStringProperty__eval="self.project.getProperty('projectfloat', None)")

		self.log.info('Example from doc is: "%s"', self.project.logConfigURL)

	def validate(self):
		pass 
