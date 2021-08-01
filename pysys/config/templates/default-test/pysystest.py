__pysys_title__   = r""" Category TODO - Test title (short, specific and sortable!) goes here TODO """ 
                         ###############################################################################

__pysys_purpose__ = r""" The purpose of this test is ... TODO.
	
	""" 
	
__pysys_authors__ = "@@USERNAME@@"
__pysys_created__ = "@@DATE@@"

#__pysys_traceability_ids__ = "BUG-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance; inherit=true"
#__pysys_skipped_reason__   = "Skipped until BUG-1234 is fixed"
#__pysys_modes__            = """ lambda helper: helper.combineModeDimensions(helper.inheritedModes, [{'mode': 'MyMode'}]) """

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		pass

	def validate(self):
		pass
	