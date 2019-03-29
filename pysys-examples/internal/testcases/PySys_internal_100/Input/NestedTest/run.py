from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.utils.pycompat import PY2, openfile
from pysys.utils.fileutils import *

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('This test is executing fine')
		self.log.info('self.input = <%s>', self.input)
		self.log.info('self.output = <%s>', self.output)
		self.mkdir('somedirectory')
		self.deletedir('somedirectory')
		openfile(toLongPathSafe(self.output+'/purgablefile.txt'), 'w').close() # should get purged, if purging is working
		with openfile(toLongPathSafe(self.output+'/somefile.txt'), 'w', encoding='ascii') as f:
			f.write(u'Hello world - logFileContents')
		self.logFileContents(self.output+'/somefile.txt')
		
		self.addOutcome(PASSED)

	def validate(self):
		pass 
