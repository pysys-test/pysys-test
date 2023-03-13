__pysys_title__   = r""" Category TODO - Test title (short, specific and sortable!) goes here TODO """ 
#                        @@LINE_LENGTH_GUIDE@@
__pysys_purpose__ = r""" """ 
	
__pysys_created__ = "@@DATE@@"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		pass

	def validate(self):
		pass
