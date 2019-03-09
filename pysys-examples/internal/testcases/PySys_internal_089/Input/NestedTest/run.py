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
		
		utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')
		self.log.info(u'Some i18n characters that only show up in run.log if utf-8: %s', utf8teststring)

		self.addOutcome(PASSED)

	def validate(self):
		pass 
