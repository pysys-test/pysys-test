__pysys_title__   = r""" Demo of pysysdirconfig.xml (test that adds to inherited directory modes) """ 
#                        ===============================================================================
__pysys_purpose__ = r""" The purpose of this test is ... TODO.
	
	""" 
	
__pysys_authors__ = "mememe"
__pysys_created__ = "1999-12-31"

__pysys_groups__           = "dirConfigSample"
__pysys_modes__            = lambda helper: helper.inheritedModes+[
				{'mode':'CompressionNone_Auth=Basic', 'compressionType':None, 'auth':'AuthBasic'}
	]

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		pass

	def validate(self):
		pass
	