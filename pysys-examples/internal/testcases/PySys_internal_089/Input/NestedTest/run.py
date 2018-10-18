import io
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		
		for p in [
			'bar/foo.default',
			'.default',
			'mydir/somefile.log',
			'mydir/other.log',
			'somefile.log',
			'mydir\\FILE2.log', # check for case sensitive matching
			'file3.log',
			'run.log',
			os.path.join(self.output, 'file4.log'),
			os.path.join(self.input, 'file5.log'),
			'run.log',
		]:
			enc = self.getDefaultFileEncoding(p)
			self.log.info('Path %s encoding=%s', p, '<None>' if enc==None else enc)
		
		
		assert self.getDefaultFileEncoding('file3.log') == self.runner.getDefaultFileEncoding('file3.log')
		self.addOutcome(PASSED)

	def validate(self):
		pass 
