import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil, json

class PySysTest(BaseTest):

	def execute(self):
		shutil.copyfile(self.input+'/pysysproject.xml', self.output+'/pysysproject.xml')
		self.pysys.pysys(self.output+'/print-json', ['print', '--json'], workingDir=self.input+'/dir1')
		self.pysys.pysys(self.output+'/print-full', ['print', '--full'], workingDir=self.input+'/dir1')

		self.pysys.pysys(self.output+'/pysys-run-modespec', ['run', 
			'Test_MultipleSubtests~MySQL_Firefox_rootmode1_SmokeTest_maxHours=1.5_fast=tRue_Subtest1_iterations=100_maxHours=-10',
			'-o', self.output+'/pysys-output1'], workingDir=self.input+'/dir1')

		self.pysys.pysys(self.output+'/pysys-run-modearg', ['run', 
			'Test_MultipleSubtests', '--mode', 'MySQL_Firefox_rootmode1_SmokeTest_maxHours=1.5_fast=tRue_Subtest1_iterations=100_maxHours=-10',
			'-o', self.output+'/pysys-output2'], workingDir=self.input+'/dir1')

		self.pysys.pysys(self.output+'/pysys-run-allmodes', ['run', 
			'Test_MultipleSubtests', '--mode', 'ALL',
			'-o', self.output+'/pysys-output3'], workingDir=self.input+'/dir1')
			
	def validate(self):
		self.copy('print-full.out', 'modes.out', mappers=[pysys.mappers.IncludeLinesMatching('(Test id:| -->)')])
		self.logFileContents('modes.out', maxLines=30)
		
		self.assertDiff('modes.out')

		for f in ['pysys-run-modespec.out', 'pysys-run-modearg.out', 'pysys-run-allmodes.out']:
			self.assertThatGrep(f, 'Test field browser=(.*)', expected="'Firefox'")
		
			# should be set from the params and also coersed to a float based on the type of the existing instance field:
			self.assertThatGrep(f, 'Test field maxHours=(.*)', expected='-10') 
		self.assertGrep('pysys-run-allmodes.out', 'Test field iterations=1000') # in SOME modes, this is a number (others a string)