__pysys_title__   = r""" waitForGrep - long line truncation and warning """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "2023-07-26"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		self.grepTruncateIfLineLongerThan = 150000-1000
		self.write_text('long-lines.txt', (15000)*'x'+'\n'+ (150000*'y'+'\n'+'signal')) # minus 1 for the \n
		self.waitForGrep('long-lines.txt', 'signal')

	def validate(self):
		self.assertGrepOfGrep('run.log', '(very long line.*);.*: x', 'very long line of 15000 characters detected in long-lines.txt during waitForGrep', 
			assertMessage='Assert warning for long line')
		self.assertGrepOfGrep('run.log', '(very long line.*);.*: y', 'very long line of 149000 characters detected in long-lines.txt during waitForGrep', 
			assertMessage='Assert truncation of long line (in this case, not enough to prevent a warning entirely)')
