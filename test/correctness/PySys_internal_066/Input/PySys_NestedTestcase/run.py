from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import threading
class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Sample log message')

		t = threading.Thread(name="MyThread", target=lambda: self.log.info('This log message is from an unregistered background thread'))
		t.start()
		t.join()


	def validate(self):
		pass 
