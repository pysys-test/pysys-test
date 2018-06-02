# -*- coding: latin-1 -*-
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import PY2
import io, locale

# contains a non-ascii � character that is different in utf-8 vs latin-1
TEST_STR = u'Hello � world' 
# use a different encoding to the default
TEST_ENCODING = 'latin-1' if locale.getpreferredencoding() == 'utf-8' else 'utf-8'

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Python local/default/preferred encoding is %s; will test with non-local encoding %s', locale.getpreferredencoding(), TEST_ENCODING)
		with io.open(self.output+'/test-local.txt', 'w', encoding=locale.getpreferredencoding()) as f:
			f.write(os.linesep.join([TEST_STR, TEST_STR, 'otherstring']))
		with io.open(self.output+'/test-nonlocal.txt', 'w', encoding=TEST_ENCODING) as f:
			f.write(os.linesep.join([TEST_STR, TEST_STR, 'otherstring']))

	def validate(self):
		# test using a unicode character string
		self.assertLineCount('test-local.txt', expr=TEST_STR, condition='==2')
		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR, condition='==0') # currently pysys cannot match character expressions in non-default files

		self.assertGrep('test-local.txt', expr=TEST_STR, contains=True)
		self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=False)

		self.waitForSignal('test-local.txt', expr=TEST_STR, condition='==2', timeout=2, abortOnError=True)

		# test using a bytes object, currently works only for Python 2
		if not PY2:
			self.log.info('skipping tests that use a bytes object as not currently supported for Python 3')
			# we could potentially get this working by having assertLineCount/assertGrep open files in 
			# binary mode if a bytes object was passed for the expr, if we wanted to
			return
		self.assertLineCount('test-local.txt', expr=TEST_STR.encode(TEST_ENCODING), condition='==0')
		self.assertLineCount('test-local.txt', expr=TEST_STR.encode(locale.getpreferredencoding()), condition='==2')
		
		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR.encode(TEST_ENCODING), condition='==2')
		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR.encode(locale.getpreferredencoding()), condition='==0')

		self.assertGrep('test-local.txt', expr=TEST_STR.encode(TEST_ENCODING), contains=False)
		self.assertGrep('test-local.txt', expr=TEST_STR.encode(locale.getpreferredencoding()), contains=True)

		self.assertGrep('test-nonlocal.txt', expr=TEST_STR.encode(TEST_ENCODING), contains=True)
		self.assertGrep('test-nonlocal.txt', expr=TEST_STR.encode(locale.getpreferredencoding()), contains=False)

		self.waitForSignal('test-local.txt', expr=TEST_STR.encode(locale.getpreferredencoding()), condition='==2', timeout=2, abortOnError=True)
		self.waitForSignal('test-nonlocal.txt', expr=TEST_STR.encode(TEST_ENCODING), condition='==2', timeout=2, abortOnError=True)