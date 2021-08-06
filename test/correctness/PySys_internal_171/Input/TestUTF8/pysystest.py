__pysys_xml_descriptor__ = """
<?xml version="1.0" encoding="utf-8"?>
<pysystest type="auto">
	<title>My UTF-8 encoded descriptor '£'</title>

	<!-- To skip the test, uncomment this (and provide a reason): <skipped reason=""/> -->
	<!-- To provide a bug/story/requirement id for requirements tracing, uncomment this: <requirement id=""/> -->

	<groups inherit="true" groups=""/>

	<modes inherit="true">
	</modes>

</pysystest>
"""

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	
	def execute(self):
		"""
		The purpose of this test is ... TODO
		
		"""
		self.log.info('Got: £')

		pass

	def validate(self):
		pass
	