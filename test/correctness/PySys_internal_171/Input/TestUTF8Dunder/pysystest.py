__pysys_title__   = """ My UTF-8 encoded descriptor '£'     <> """ 

__pysys_xml_descriptor__ = r"""
	<?xml version="1.0" encoding="utf-8"?>
	<pysystest>
		<!-- To skip the test, uncomment this (and provide a reason): <skipped reason=""/> -->
		<!-- To provide a bug/story/requirement id for requirements tracing, uncomment this: <requirement id=""/> -->

		<groups inherit="true" groups="my-xml-group"/>

		<modes inherit="true">
		</modes>

	</pysystest>
	"""

import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	
	def execute(self):
		self.log.info('Got: £')
		assert self.descriptor.groups == ['my-xml-group'], self.descriptor.groups

		pass

	def validate(self):
		pass
	

# unusually, put this after some import statements to check it still works
# the above "pysys.basetest.BaseTest" reference would break without the "pysys.baserunner" at the bottom of descriptor.py
__pysys_purpose__ = """ The purpose of this test is ... 
	very interesting
	
		oh yeah!""" 
