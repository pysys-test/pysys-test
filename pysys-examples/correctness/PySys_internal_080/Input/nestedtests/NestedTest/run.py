from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *


class PySysTest(BaseTest):
	def execute(self):
		# wait a random amount of time up to a second
		self.startProcessMonitor(process=int(self.pidToMonitor), file='monitor-legacy.tsv', interval=0.1)
		self.waitForGrep('monitor-legacy.tsv', expr='.', condition='>=5', ignores=['#.*'])
		
	def validate(self):
		pass 
