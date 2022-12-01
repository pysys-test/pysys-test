__pysys_title__   = r""" Assertions - waitForGrep - timeout while iterating through lines""" 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-12-01"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *
from pysys.exceptions import AbortExecution

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):
		self.write_text('file.txt', '\n'.join(
			[
				'first line',
				'10k '+'l' * 10000,
				'20k '+'l' * 20000,
				'30k '+'l' * 20000,
				'40k '+'l' * 20000,
				'100k '+'l' * 100000,
			]+
			['x' for l in range(10000-10)]))

		# deliberately make each iteration take a long time
		lineno = [0] 
		def sleepyMapper(line):
			lineno[0] += 1
			if line.startswith('first line'): # sleep every time round the loop, to trigger the timeout later
				self.wait(1)
			return line

		try:
			self.waitForGrep('file.txt', 'ax', timeout=3, errorExpr=['ay'], 
				mappers=[sleepyMapper] )
		except AbortExecution as ex:
			self.assertThat('msg.startswith(expected)', msg=str(ex), expected='Waiting for "ax" in file.txt timed out after', override=True)
		else:
			self.addOutcome(FAILED, 'Did not get exception as expected')
		
	def validate(self):
		self.assertGrep('run.log', 'very long line of ..... characters detected in file.txt during waitForGrep')
		self.assertLineCount('run.log', 'very long line ', condition='<10')