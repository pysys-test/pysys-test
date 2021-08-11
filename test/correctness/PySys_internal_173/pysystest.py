__pysys_title__ = r"""pysys.py - make with validator"""

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.copy(self.input, 'tests')
		self.pysys.pysys('make-invalid-char', ['make', 'MyTest-WithHyphen'], workingDir=self.output+'/tests', expectedExitStatus='!=0')
		self.logFileContents('make-invalid-char.err')
		self.pysys.pysys('make-invalid-char-override', ['make', 'MyTest-WithHyphenOverride', '--skipValidation'], workingDir=self.output+'/tests')
		self.pysys.pysys('make-suffix-no-prefixes', ['make'], workingDir=self.output+'/tests', expectedExitStatus='!=0')
		
		self.mkdir('tests/MyPrefix_04')
		self.pysys.pysys('make-invalid-numeric-suffix', ['make', 'MyPrefix_05'], workingDir=self.output+'/tests', expectedExitStatus='!=0')
		
		# should generate 10 and 11, as recommended by the validator
		self.pysys.pysys('make-auto', ['make'], workingDir=self.output+'/tests')
		self.pysys.pysys('make-auto2', ['make'], workingDir=self.output+'/tests')

		self.mkdir('tests/MyPrefix_0101')
		# will take padding from the largest number
		self.pysys.pysys('make-auto3', ['make'], workingDir=self.output+'/tests')

		self.mkdir('tests/MyOtherPrefix_0101')
		self.pysys.pysys('make-multiple-prefixes', ['make'], workingDir=self.output+'/tests', expectedExitStatus='!=0')
		
	def validate(self):
		self.assertThatGrep('make-invalid-char.err', '.*',
			expected='Test id "MyTest-WithHyphen" was rejected by validator: Test ids containing - are not permitted (if needed, use --skipValidation to disable checking)')

		self.assertThatGrep('make-suffix-no-prefixes.err', '.*', 
			expected='Please specify the test id to be created.')

		self.assertThatGrep('make-invalid-numeric-suffix.err', '.*', 
			expected='Test id "MyPrefix_05" was rejected by validator: This test id conflicts with an existing test (if needed, use --skipValidation to disable checking)')

		self.assertThatGrep('make-multiple-prefixes.err', '.*', 
			expected='When using numeric test ids you should use the same prefix for all tests in each directory, but multiple prefixes were found: MyOtherPrefix_, MyPrefix_')
	
		self.assertThatGrep('make-auto.out', ' INFO +(.*)', 'value.startswith(expected)',
			expected="Called validateTestId for numericSuffix='05' and parentDir=")

		self.assertThat('finalTestDirs == expected', 
			finalTestDirs=sorted(os.listdir(self.output+'/tests')), expected=sorted([
				# static content:
				'extrapath', 'pysysproject.xml', 'MyNestedTestcase', 
				# created explicitly by test:
				'MyPrefix_04', 'MyPrefix_0101', 'MyOtherPrefix_0101', 
				# created by pysys make explicitly:
				'MyTest-WithHyphenOverride',
				# auto-created:
				'MyPrefix_10', 'MyPrefix_11', 
				'MyPrefix_0102', # takes padding from largest number so far
				
		]))
		
