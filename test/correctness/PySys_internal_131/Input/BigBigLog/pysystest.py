__pysys_title__   = r""" Test with greater than 4k of run.log """

from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info("Start of the test")
		for i in range(1000):
			self.log.info("Spam spam spam spam")
		self.log.info("End of the test")
		self.addOutcome(FAILED, "This message should appear in the Github annotation")

	def validate(self):
		pass 
