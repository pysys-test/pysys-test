# -*- coding: latin-1 -*-
from pysys.constants import *
from pysys.basetest import BaseTest
import io, locale

# contains a non-ascii � character that is different in utf-8 vs latin-1
TEST_STR = u'Hello � world' 
# use a different encoding to the default/local encoding
TEST_ENCODING = 'latin-1' if PREFERRED_ENCODING.lower() == 'utf-8' else 'utf-8'

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Python local/default/preferred encoding is %s; will test with non-local encoding %s', PREFERRED_ENCODING, TEST_ENCODING)
		if PREFERRED_ENCODING in ['ANSI_X3.4-1968', 'ascii']: self.skipTest('cannot run in ASCII locale')

		with io.open(self.output+'/test-local.txt', 'w', encoding=PREFERRED_ENCODING) as f:
		#with open(self.output+'/test-local.txt', 'w') as f:
			f.write(os.linesep.join([TEST_STR, TEST_STR, 'otherstring']))
		with io.open(self.output+'/test-nonlocal.txt', 'w', encoding=TEST_ENCODING) as f:
			f.write(os.linesep.join([TEST_STR, TEST_STR, 'otherstring']))

	def validate(self):
		exceptionReadingNonLocal = TEST_ENCODING != 'utf-8'

		# test using a unicode character string. weirdly python2 matches 
		# re.search(TEST_STR,TEST_STR.encode('latin-1'))==True but
		# re.search(TEST_STR,TEST_STR.encode('utf-8'))==False
		# (python 3 doesn't have that issue). since the goal here is mostly to check current behaviour 
		# hasn't changed, just skip the weirdness
		self.assertLineCount('test-local.txt', expr=TEST_STR, condition='==2')
		self.assertGrep('test-local.txt', expr=TEST_STR, contains=True)
		self.waitForGrep('test-local.txt', expr=TEST_STR, condition='==2', timeout=2, abortOnError=True)

		if not exceptionReadingNonLocal:
			self.assertLineCount('test-nonlocal.txt', expr=TEST_STR, condition='==0')
			self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=False)
		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR, condition='==2', encoding=TEST_ENCODING)

		self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=True, encoding=TEST_ENCODING)
		
		# smoke test this one too
		self.waitForGrep('test-nonlocal.txt', expr=TEST_STR, condition='==2', timeout=2, abortOnError=True, encoding=TEST_ENCODING)

		# test using a bytes object, currently works only for Python 2
		self.log.info('skipping tests that use a bytes object as not currently supported for Python 3')
		# we could potentially get this working by having assertLineCount/assertGrep open files in 
		# binary mode if a bytes object was passed for the expr, if we wanted to
