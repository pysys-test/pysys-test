import io, locale, os
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.utils.pycompat import *

class PySysTest(BaseTest):
	def execute(self):
		self.utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')
		#self.log.info('XXXXXXX %s'%self.utf8teststring.encode('utf-8'))

		self.log.info('Nested test: preferred encoding=%s, stdout encoding=%s, PYSYS_COLOR=%s', locale.getpreferredencoding(), sys.stdout.encoding, os.getenv('PYSYS_COLOR','False'))
		#self.log.info('Nested test: env=%s'%os.environ)
		
		# contains chars that are not representable in iso8859-1
		utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')
		with io.open(self.output+'/utf8.txt', 'w', encoding='utf-8') as f:
			f.write(u'Text file contents: %s end'%utf8teststring)
		self.log.info(u'Log message including i18n string %s end', utf8teststring) # unicode string
		
		self.log.info(b'Log bytes message without i18n %s', b'string') # byte string - fine
		if not PY2: # doesn't work in python 2
			self.log.info(b'Log bytes message including i18n string %s end'%utf8teststring.encode('utf-8')) # byte string
		
		self.log.info('Logging file using latin-1 encoding:') # check logging still works
		assert self.logFileContents('utf8.txt', encoding='latin-1') # deliberately use wrong encoding
		self.log.info('Logging file using ascii encoding:') # check logging still works
		assert self.logFileContents('utf8.txt', encoding='ascii') # deliberately use wrong encoding
		self.log.info('Logging file using utf8 encoding:') # check logging still works
		assert self.logFileContents('utf8.txt', encoding='utf-8') # this should actually work, if output locale permits it
		self.log.info('Logging file using default encoding:') # check logging still works
		assert self.logFileContents('utf8.txt') # use default encoding even though it's ASCII and doesn't support this

		self.log.info('Other log message') # check logging still works

		self.addOutcome(FAILED, 'outcome reason %s end'%utf8teststring)
	def validate(self):
		pass 
