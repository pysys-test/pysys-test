# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob

class PySysTest(BaseTest):

	def execute(self):
		
		shutil.copytree(self.input, self.output+'/test')

		l = {}
		exec(open(self.input+'/../../../utilities/resources/runpysys.py').read(), {}, l) # define runPySys
		runPySys = l['runPySys']
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
		self.assertGrep('pysys.out', expr='Path run.log encoding=euc_kr')
		self.assertGrep('pysys.out', expr='file4.log encoding=euc_kr')
		self.assertGrep('pysys.out', expr='file5.log encoding=euc_kr')
		
		self.log.info('')
		self.log.info('Checking pysys-examples project defaults:')
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.xml"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.XML"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("mydir/foo.yaml"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.json"), repr('utf-8'))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.whatever"), repr(None))
		self.assertThat('self.getDefaultFileEncoding(%s) == %s', repr("foo.log"), repr(None))
