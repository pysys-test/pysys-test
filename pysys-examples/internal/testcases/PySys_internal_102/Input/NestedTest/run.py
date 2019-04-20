import io

from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):	
		for base in ['.', 'dir2']:
			self.mkdir(base)
			for name in [u'foo', u'a-foo', u'notthis', u'foo-b']:
				with io.open(self.output+'/'+base+'/'+name, 'w', encoding='ascii') as f:
					f.write(name)
	
		self.log.info('End of execute()')

	def validate(self):
		pass 
