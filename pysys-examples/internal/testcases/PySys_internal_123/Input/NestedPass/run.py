from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
import pysys.utils.allocport

class PySysTest(BaseTest):
	def execute(self):
		# call it first to make sure it also works 2nd time
		pysys.utils.allocport.getServerTCPPorts()
		
		self.write_text('server_ports.txt', u'\n'.join(map(str, sorted(list(pysys.utils.allocport.getServerTCPPorts())))))
	def validate(self):
		pass 
