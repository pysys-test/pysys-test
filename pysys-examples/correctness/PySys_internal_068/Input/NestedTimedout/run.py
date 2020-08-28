# -*- coding: latin-1 -*-

from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 

class PySysTest(BaseTest):
	def execute(self):
		self.addOutcome(TIMEDOUT, 'Reason for timed out outcome is general tardiness - %s'%TEST_STR)
	def validate(self):
		pass 
