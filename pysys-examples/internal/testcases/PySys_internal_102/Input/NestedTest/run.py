# -*- coding: latin-1 -*-
import io

from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):	
		for base in [u'.', u'dir2']:
			self.mkdir(base)
			for name in [u'foo', u'a-foo', u'notthis', u'foo-b']:
				with io.open(self.output+u'/'+base+u'/'+name, 'w', encoding='utf-8') as f:
					f.write(name)
	
		self.log.info('End of execute()')

	def validate(self):
		pass 
