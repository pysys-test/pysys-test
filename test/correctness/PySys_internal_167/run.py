import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, json

class PySysTest(BaseTest):

	def execute(self):
		for subtest in os.listdir(self.input):
			self.pysys.pysys(subtest, ['print', '--full'], expectedExitStatus='!=0', workingDir=self.input+'/'+subtest)
			if subtest != 'syntaxerror':
				self.assertThatGrep(subtest+'.err', '.+', 'value.startswith(prefix) and expected in value', prefix='ERROR: Invalid modes configuration in ', expected=subtest)
			self.log.info('')

	def validate(self):
		self.assertThatGrep('differentparamkeys.err', '.+', 'expected in value', 
			expected=": The same mode parameter keys must be given for every mode in the list, but found ['param1', 'param2'] parameters for \"Baz_bar\" different to ['param1']")

		self.assertThatGrep('doubleunderscore.err', '.+', 'expected in value', 
			expected=": Invalid mode \"a__b\" cannot contain double underscore")

		self.assertThatGrep('dupmode.err', '.+', 'expected in value', 
			expected=': Duplicate mode "MyMode"')

		self.assertThatGrep('illegalparamkey.err', '.+', 'expected in value', 
			expected=': Illegal mode parameter name - cannot start with underscore: __paramName')
			
		self.assertThatGrep('inherit.err', '.+', 'expected in value', 
			expected=': Cannot use the legacy inherit= attribute when using the modern Python lambda to define modes')
			
		self.assertThatGrep('nondict.err', '.+', 'expected in value', 
			expected=': Each mode must be a {...} dict but found unexpected object 12345 (int)')

		self.assertThatGrep('nonlist.err', '.+', 'expected in value', 
			expected=": Expecting a list of modes, got a str: 'abcdef'")

		self.assertThatGrep('syntaxerror.err', 'ERROR.+', 'expected in value and "line 3" in value', 
			expected='SyntaxError - ')
