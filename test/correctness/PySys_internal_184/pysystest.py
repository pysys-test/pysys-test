__pysys_title__   = r""" Writers - PYSYS_CONSOLE_FAILURE_ANNOTATIONS """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-03-11"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

import pysys.basetest, pysys.mappers
from pysys.constants import *

import os, sys, math, shutil, glob
import json

from pysysinternalhelpers import PySysTestHelper


class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):

		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir'], workingDir=self.input, 
			environs={
				# this is a good test in which to test the default behaviour works when enabled
				'PYSYS_CONSOLE_FAILURE_ANNOTATIONS':'##CUSTOM_ANNOTATION runpy=@testFile/@; json=@json@',
				'PYSYS_CONSOLE_FAILURE_ANNOTATIONS_INCLUDE_OUTCOMES':'*',
			}, expectedExitStatus='==2')
		self.logFileContents('pysys-run.out',includes=['##CUSTOM_ANNOTATION.*'])
		
	def validate(self):
		self.assertThatGrep('pysys-run.out', '##CUSTOM_ANNOTATION .*NestedTimedout', 
			'expected in value', expected='NestedTimedout/run.py;', 
			assertMessage='Check locating of the testFile works for old-style XML test')
		self.assertThatGrep('pysys-run.out', '##CUSTOM_ANNOTATION .*NestedSkipped', 
			'expected in value', expected='NestedSkipped/pysystest.py;', 
			assertMessage='Check locating of the testFile works for new-style pysystest.py test')
			

		self.assertThatGrep('pysys-run.out', '##CUSTOM_ANNOTATION .*MyNestedTestcase.*; json=(.*)', 
			'expected == json.loads(value)["testFile"]', expected="pysystest.py", 
			assertMessage='Check testFile from JSON is correct')

			
		self.assertThatGrep('pysys-run.out', '##CUSTOM_ANNOTATION .*MyNestedTestcase.*; json=(.*)', 
			'expected <= set(json.loads(value).keys())', expected={'title', 'testId', 'outcome'}, 
			assertMessage='Check the JSON parses and the main expected keys are present')
			
			
		self.assertLineCount('pysys-run.out', '##CUSTOM_ANNOTATION ', condition='==6')