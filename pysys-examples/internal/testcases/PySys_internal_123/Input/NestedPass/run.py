from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import pysys.utils.allocport

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Ephemeral port range is: %d-%d'%pysys.utils.allocport.getEphemeralTCPPortRange())
	def validate(self):
		pass 
