# -*- coding: latin-1 -*-
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import PY2
import io, locale

# contains a non-ascii £ character that is different in utf-8 vs latin-1
TEST_STR = u'Hello £ world' 
# use a different encoding to the default/local encoding
TEST_ENCODING = 'latin-1' if locale.getpreferredencoding() == 'utf-8' else 'utf-8'

class PySysTest(BaseTest):
	def execute(self):
		self.log.info('Python local/default/preferred encoding is %s; will test with non-local encoding %s', locale.getpreferredencoding(), TEST_ENCODING)
		with io.open(self.output+'/test-nonlocal.txt', 'w', encoding=TEST_ENCODING) as f:
			f.write(os.linesep.join([TEST_STR, TEST_STR, 'otherstring']))
		self.__myDefaultEncoding = None

	def validate(self):
		self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=False) # without encoding arg, won't work

		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR, condition='==2', encoding=TEST_ENCODING)
		self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=True, encoding=TEST_ENCODING)
		self.waitForSignal('test-nonlocal.txt', expr=TEST_STR, condition='==2', timeout=2, abortOnError=True, encoding=TEST_ENCODING)
		self.assertLastGrep('test-nonlocal.txt', expr=TEST_STR, contains=True, ignores=['^$', 'otherstring'], encoding=TEST_ENCODING)
		self.assertOrderedGrep('test-nonlocal.txt', exprList=[TEST_STR, TEST_STR], encoding=TEST_ENCODING)
		self.assertTrue(self.logFileContents('test-nonlocal.txt', encoding=TEST_ENCODING))
		self.assertDiff('test-nonlocal.txt', 'test-nonlocal.txt', filedir1=self.output, filedir2=self.output, encoding=TEST_ENCODING)
		self.assertThat('%s==%s', repr(TEST_STR), repr(self.getExprFromFile('test-nonlocal.txt', TEST_STR, encoding=TEST_ENCODING)))
		
		self.log.info('')
		self.log.info('now testing using getDefaultFileEncoding:')
		self.__myDefaultEncoding = TEST_ENCODING
		self.assertLineCount('test-nonlocal.txt', expr=TEST_STR, condition='==2')
		self.assertGrep('test-nonlocal.txt', expr=TEST_STR, contains=True)
		self.waitForSignal('test-nonlocal.txt', expr=TEST_STR, condition='==2', timeout=2, abortOnError=True)
		self.assertLastGrep('test-nonlocal.txt', expr=TEST_STR, contains=True, ignores=['^$', 'otherstring'])
		self.assertOrderedGrep('test-nonlocal.txt', exprList=[TEST_STR, TEST_STR])
		self.assertTrue(self.logFileContents('test-nonlocal.txt'))
		self.assertDiff('test-nonlocal.txt', 'test-nonlocal.txt', filedir1=self.output, filedir2=self.output)
		self.assertThat('%s==%s', repr(TEST_STR), repr(self.getExprFromFile('test-nonlocal.txt', TEST_STR)))
		
	
	def getDefaultFileEncoding(self, file, **xargs):
		if self.__myDefaultEncoding != None:
			self.log.info('  called getDefaultFileEncoding for %s with %s', file, xargs)
		return self.__myDefaultEncoding
	
		