from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

import logging
import pysys

class PySysTest(BaseTest):
	def execute(self):
		l = logging.getLogger('myloggercat')
		l.warn('Hello at warn')
		l.info('Hello at info')
		l.debug('Hello at debug')
		
	def validate(self):
		pass 
