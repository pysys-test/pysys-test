import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, json

class PySysTest(BaseTest):

	def execute(self):
		for subtest in os.listdir(self.input):
			self.pysys.pysys(subtest, ['print', '--full'], expectedExitStatus='!=0', workingDir=self.input+'/'+subtest)
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
			expected=': Cannot use the legacy inherit= attribute when using the modern Python eval string to define modes')
			
		self.assertThatGrep('nondict.err', '.+', 'expected in value', 
			expected=': Expecting mode dict but got 12345')

		self.assertThatGrep('nonlist.err', '.+', 'expected in value', 
			expected=": Expecting a list of modes, got a dict: {'a': 'b'}")

		self.assertThatGrep('syntaxerror.err', '.+', 'expected in value', 
			expected='SyntaxError - invalid syntax (<string>, line 3)')
