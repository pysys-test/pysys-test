# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		self.copy(self.input, self.output+'/test')

		# use multiple cycles since the buffering is different
		try:
			runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir'], workingDir=self.output+'/test')
		finally:
			self.logFileContents('pysys.out', maxLines=0)
			self.logFileContents('pysys.err', maxLines=0)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)

		# check that earliest matching rule works
		self.assertGrep('pysys.out', expr='Path bar/foo.default encoding=<None>')
		self.assertGrep('pysys.out', expr='Path .default encoding=<None>')
		self.assertGrep('pysys.out', expr='mydir/somefile.log encoding=cp775')
		self.assertGrep('pysys.out', expr='Path mydir/other.log encoding=euc_kr')
		self.assertGrep('pysys.out', expr='Path somefile.log encoding=euc_jp')
		self.assertGrep('pysys.out', expr='Path mydir.FILE2.log encoding=iso8859_2') # case insensitivity (want same behaviour on all platforms)
		self.assertGrep('pysys.out', expr='Path file3.log encoding=euc_kr')
		self.assertGrep('pysys.out', expr='Path run.log encoding=utf-8')
		self.assertGrep('pysys.out', expr='file4.log encoding=euc_kr')
		self.assertGrep('pysys.out', expr='file5.log encoding=euc_kr')

		# a unicode string; contains chars that are not representable in iso8859-1
		utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')
		self.assertGrep('myoutdir/NestedTest/run.log', expr=u'Some i18n characters that only show up in run.log if utf-8: %s'%utf8teststring, encoding='utf-8')
		
		self.log.info('')
		self.log.info('Checking project defaults (which at least for now are the same as the sample project):')
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.xml"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.XML"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("mydir/foo.yaml"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.json"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.whatever"), repr(None))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.log"), repr(None))

		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("run.log"), repr('utf-8'))
