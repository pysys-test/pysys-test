# -*- coding: latin-1 -*-
import gzip
import io, locale
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import PY2
from pysys.utils.fileunzip import *

# for test string, use all possible newline types, and also some non-ascii characters that would 
# trip up any attempt to decode using a specific encoding
TEST_BYTES = b'A\nB\r\nC\n\rD'+u'£'.encode('latin-1')+u'£'.encode('utf-8')

class PySysTest(BaseTest):
	def execute(self):
		with gzip.open(self.mkdir(self.output+'/bin')+'/test.txt.gz', 'wb') as f:
			f.write(TEST_BYTES)
		with gzip.open(self.mkdir(self.output+'/txt')+'/test.txt.gz', 'wb') as f:
			f.write(TEST_BYTES)
		
		self.log.info('unzipping bin with binary=True')
		unzipall(self.output+'/bin', binary=True) #default is replace=True
		self.log.info('unzipping bin txt with binary=False')
		unzip(self.output+'/txt/test.txt.gz') #default is replace=False
		

	def validate(self):
		# check the replace flag was honoured
		self.assertThat('not os.path.exists(%s)', repr(self.output+'/bin/test.txt.gz'))
		self.assertThat('os.path.exists(%s)', repr(self.output+'/txt/test.txt.gz'))

		self.log.info('Test bytes are:                        %s', (TEST_BYTES.replace(b'\n', b'\\n').replace(b'\r', b'\\r')).decode(locale.getpreferredencoding(), 'replace'))

		with open(self.output+'/bin/test.txt', 'rb') as f:
			# no corruption for binary mode
			self.assertThat('%s == %s', repr(f.read()), repr(TEST_BYTES))
			
		with open(self.output+'/txt/test.txt', 'rb') as f:
			bytes = f.read()
			self.log.info('Bytes read out of non-binary file are: %s', bytes.replace(b'\n', b'\\n').replace(b'\r', b'\\r').decode(locale.getpreferredencoding(), 'replace'))
			# in non-binary mode, according to the python docs we expect conversion of \n to \r\n on windows, and no change on unix
			# (not convinced this is very useful behaviour, but testing this to avoid breaking compatibility)
			self.assertThat('%s == %s', repr(bytes), repr(
				TEST_BYTES.replace(b'\n', b'\r\n') if PLATFORM=='win32' else TEST_BYTES
			))

