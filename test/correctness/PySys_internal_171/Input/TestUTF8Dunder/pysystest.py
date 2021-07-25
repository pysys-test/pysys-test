__pysystest_title__   = """ My UTF-8 encoded descriptor '£'     <> """ 

__pysystest_purpose__ = """ The purpose of this test is ... 
	very interesting
	
		oh yeah!""" 


import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	"""
	<?xml version="1.0" encoding="utf-8"?>
	<pysystest>
		<!-- To skip the test, uncomment this (and provide a reason): <skipped reason=""/> -->
		<!-- To provide a bug/story/requirement id for requirements tracing, uncomment this: <requirement id=""/> -->

		<groups inherit="true" groups=""/>

		<modes inherit="true">
		</modes>

	</pysystest>
	"""
	
	def execute(self):
		self.log.info('Got: £')

		pass

	def validate(self):
		pass
	
