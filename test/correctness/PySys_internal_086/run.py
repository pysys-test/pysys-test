# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.pycompat import *
import os, sys, math, shutil, glob, locale

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):
	# a unicode string; contains chars that are not representable in iso8859-1
	utf8teststring = b'utf8_European\\xe1\\xc1x\\xdf_Katakana\\uff89\\uff81\\uff90\\uff81\\uff7f\\uff78\\uff81\\uff7d\\uff81\\uff7f\\uff76\\uff72\\uff7d\\uff84_Hiragana\\u65e5\\u672c\\u8a9e_Symbols\\u2620\\u2622\\u2603_abc123@#\\xa3!~=\\xa3x'.decode('unicode_escape')
	
	supportsAsciiLANG = PLATFORM != 'darwin' # macos doesn't seem to support overriding LANG, so skip that bit of the test

	def execute(self):
		
		self.log.info('parent test: preferred encoding=%s, stdout encoding=%s', locale.getpreferredencoding(), sys.stdout.encoding)

		self.copy(self.input, self.output+'/test')
		# make testRootDir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		# use multiple cycles since the buffering is different
		
		runid = 'defaultrun'
		
		processes = []

		# ad-hoc testing showed behaviour is affected by a stunningly complex set of variables - this is should give reasonable 
		# coverage of the combinations like to cause trouble
		
		# nb: on python2, redirecting stdout (as we always do here) results in the child pysys having sys.stdout.encoding=None 
		# which is an important code path to test; for python 3 encoding is always set to the preferred encoding so there's no 
		# extra code path to test; but to maintain coverage of the encoding combinations we need to explicitly set it 
		# (since otherwise python3 would set it to match the pre-hacked lang on windows, which would not give sensible results)
		
		def createenv(base, LANG=None):
			r = dict(base)
			if LANG:
				if LANG=='ascii' and not IS_WINDOWS: LANG = 'C'
				r['LANG'] = LANG # sets getpreferredencoding (with monkey-patch hack in runner to make it work on windows)
				r['LANGUAGE'] = LANG # needed on some Ubuntu versions
				r['LC_ALL'] = LANG
				r['LC_CTYPE'] = LANG
				
				# to allow us to test i18n cases, need to forcibly disable Python 3.7's attempt to use UTF-8 when in a C locale
				r['PYTHONCOERCECLOCALE'] = '0' 
				if 'utf-8' not in LANG: r['PYTHONUTF8'] = '0'
				
			return r
		
		if self.supportsAsciiLANG:
			runid=os.path.basename(self.mkdir('default=ascii,stdout=utf8,color=true,threads=1'))
			processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '1'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
					'TEST_RUNID':runid,
					'PYSYS_COLOR':'true', # this affects the stdout stream
					'PYTHONIOENCODING':'utf-8', # sets stdout encoding
					}, LANG='ascii')))
			runid=os.path.basename(self.mkdir('default=ascii,stdout=utf8,color=true,threads=2'))
			processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '2'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
					'TEST_RUNID':runid,
					'PYSYS_COLOR':'true', # this affects the stdout stream
					'PYTHONIOENCODING':'utf-8', # sets stdout encoding
					}, LANG='ascii')))
			runid=os.path.basename(self.mkdir('default=ascii,stdout=ascii,color=false,threads=1'))
			processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '1'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
					'TEST_RUNID':runid,
					'PYSYS_COLOR':'false', # this affects the stdout stream
					'PYTHONIOENCODING':'ascii', # sets stdout encoding
					}, LANG='ascii')))
			runid=os.path.basename(self.mkdir('default=ascii,stdout=none,color=true,threads=1')) # also progress, why not!
			processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '1', '--progress'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
					'TEST_RUNID':runid,
					'PYSYS_COLOR':'true', # this affects the stdout stream
					'PYTHONIOENCODING':None if PY2 else 'ascii', # sets stdout encoding
					}, LANG='ascii')))
			runid=os.path.basename(self.mkdir('default=ascii,stdout=none,color=false,threads=2'))
			processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '2'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
					'TEST_RUNID':runid,
					'PYSYS_COLOR':'false', # this affects the stdout stream
					'PYTHONIOENCODING': None if PY2 else 'ascii', # sets stdout encoding
					}, LANG='ascii')))
				
		runid=os.path.basename(self.mkdir('default=utf8,stdout=ascii,color=true,threads=2'))
		processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '2'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
				'TEST_RUNID':runid,
				'PYSYS_COLOR':'true', # this affects the stdout stream
				'PYTHONIOENCODING':'ascii', # sets stdout encoding
				}, LANG='en_US.utf-8')))
		runid=os.path.basename(self.mkdir('default=utf8,stdout=none,color=true,threads=2'))
		processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '2'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
				'TEST_RUNID':runid,
				'PYSYS_COLOR':'true', # this affects the stdout stream
				'PYTHONIOENCODING':None if PY2 else 'utf-8', # sets stdout encoding
				}, LANG='en_US.utf-8')))
		runid=os.path.basename(self.mkdir('default=utf8,stdout=utf8,color=false,threads=2'))
		processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '2'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
				'TEST_RUNID':runid,
				'PYSYS_COLOR':'false', # this affects the stdout stream
				'PYTHONIOENCODING':'utf-8', # sets stdout encoding
				}, LANG='en_US.utf-8')))
		runid=os.path.basename(self.mkdir('default=local,stdout=local,color=true,threads=2,debug=true'))
		processes.append(runPySys(self, runid+'/pysys', ['run', '-o', self.output+'/'+runid+'/testoutput', '--record', '-c', '2', '--threads', '1', '-v', 'debug'], workingDir='test', ignoreExitStatus=True, state=BACKGROUND, environs=createenv({
				'TEST_RUNID':runid,
				'PYSYS_COLOR':'true', # this affects the stdout stream
				'PYTHONIOENCODING':None, # sets stdout encoding
				}))) #'LANG':None # sets getpreferredencoding (with monkey-patch hack in runner to make it work on windows)
			
		for p in processes:
			self.waitProcess(p, timeout=60)
			if p.exitStatus != 2:
				self.addOutcome(FAILED, 'Got unexpected failure from %s'%p)

	def validate(self):
		runs = [
			'default=utf8,stdout=ascii,color=true,threads=2',
			'default=utf8,stdout=none,color=true,threads=2',
			'default=utf8,stdout=utf8,color=false,threads=2',
			'default=local,stdout=local,color=true,threads=2,debug=true',
		]
		
		if self.supportsAsciiLANG:
			runs.extend([
			'default=ascii,stdout=utf8,color=true,threads=1',
			'default=ascii,stdout=utf8,color=true,threads=2',
			'default=ascii,stdout=ascii,color=false,threads=1',
			'default=ascii,stdout=none,color=true,threads=1',
			'default=ascii,stdout=none,color=false,threads=2'])


			self.logFileContents('default=local,stdout=local,color=true,threads=2,debug=true'+'/pysys.out', maxLines=0)

			
			# sanity check that nested python is running with expected locale, which rest of testcase assumes
			if PY2:
				self.assertGrep('default=ascii,stdout=none,color=false,threads=2'+'/pysys.out', expr='Nested test: preferred encoding=(ascii|ANSI_X3.4-1968), stdout encoding=None')
			self.assertGrep('default=ascii,stdout=utf8,color=true,threads=2'+'/pysys.out', expr='Nested test: preferred encoding=(ascii|ANSI_X3.4-1968), stdout encoding=(utf-8)', encoding='utf-8')
			self.assertGrep('default=utf8,stdout=ascii,color=true,threads=2'+'/pysys.out', expr='Nested test: preferred encoding=(utf-8|UTF-8), stdout encoding=(ascii|ANSI_X3.4-1968)')


			# some checks that are only needed for one of the runs
			self.log.info('')
			runid='default=ascii,stdout=ascii,color=false,threads=1'
			self.assertGrep('%s/xmlresults.xml'%runid, expr='<result id="NestedFail" outcome=', encoding='utf-8')
			self.assertGrep('%s/xmlresults.xml'%runid, expr='<result id="NestedFail" outcome="FAILED">', encoding='utf-8')
			self.assertGrep('%s/xmlresults.xml'%runid, expr='<outcomeReason>outcome reason .*end</outcomeReason>', encoding='utf-8')

			# even if the run.log file can't represent all the chars, the utf-8 XML ought to
			self.assertGrep(runid+'/junitresults/TEST-NestedFail.1.xml', expr='Log message including i18n string %s end.*'%self.utf8teststring, encoding='utf-8')
			
			self.assertGrep(runid+'/junitresults/TEST-NestedFail.1.xml', expr='Log bytes message without i18n.*string', encoding='utf-8') # byte format strings are formatted differently in py 2 vs 3
			
			if not PY2:
				self.assertGrep(runid+'/junitresults/TEST-NestedFail.1.xml', expr='Log bytes message including i18n string .+ end', encoding='utf-8')
			
			self.assertGrep(runid+'/junitresults/TEST-NestedFail.1.xml', expr='<failure message="FAILED: outcome reason .+end"', encoding='utf-8')
			self.assertGrep(runid+'/junitresults/TEST-NestedFail.1.xml', expr='<failure message="FAILED: outcome reason %s end"'%self.utf8teststring, encoding='utf-8')

			# specific checks for specific runs
			self.log.info('')
			self.assertGrep('default=local,stdout=local,color=true,threads=2,debug=true/pysys.out', expr=' DEBUG ', encoding=locale.getpreferredencoding())
			self.assertGrep('default=local,stdout=local,color=true,threads=2,debug=true/pysys.out', expr='Failed to load coloring library', encoding=locale.getpreferredencoding(), contains=False)

		i = 0
		for runid in runs:
			i+=1
			self.log.info('')
			self.log.info('-------------')

			runlog_enc = 'utf-8' if 'default=utf8' in runid else 'ascii'
			stdout_enc = 'utf-8' if 'stdout=utf8' in runid else 'ascii'
			if 'stdout=none' in runid: stdout_enc = runlog_enc
			if 'default=local,stdout=local' in runid:
				runlog_enc = stdout_enc = locale.getpreferredencoding().lower()

			self.log.info('Run %d: %s (run.log=%s stdout=%s)', i, runid, runlog_enc, stdout_enc)
			
			self.logFileContents(runid+'/pysys.err')
			self.logFileContents(runid+'/pysys.out', includes=['Nested test: .*'], encoding=stdout_enc)
			
			self.assertGrep(runid+'/pysys.err', expr='.+' , contains=False, encoding=stdout_enc)
			self.assertGrep(runid+'/pysys.out', expr='(Traceback.*|caught .*)', contains=False, encoding=stdout_enc)
			self.assertGrep(runid+'/pysys.out', expr='failed to write buffered test output', contains=False, encoding=stdout_enc)
			self.assertGrep(runid+'/pysys.out', expr='Unicode(Decode|Encode)Error.*' , contains=False, encoding=stdout_enc)

			
			for outfile in [runid+'/pysys.out', runid+'/testoutput/NestedFail/cycle1/run.log']:
				enc = runlog_enc if outfile.endswith('run.log') else stdout_enc
				
				# test messages aren't entirely lost
				self.assertGrep(outfile, expr='Log message including i18n string .+ end', encoding=enc)
				if not PY2: # in python2 this would give an exception in the run.py so we don't even attempt it
					self.assertGrep(outfile, expr='Log bytes message including i18n string .+ end', encoding=enc)
				self.assertGrep(outfile, expr='Other log message', encoding=enc)
				self.assertGrep(outfile, expr='Test outcome reason: %soutcome reason.*end'%('.*' if outfile.endswith('.out') else ''), encoding=enc)

				if enc == 'utf-8':
					self.assertGrep(outfile, expr=u'Test outcome reason: .*outcome reason %s end'%self.utf8teststring, encoding=enc)
				elif enc == 'ascii': # ensure we have some suitable replacement chars
					self.assertGrep(outfile, expr='Test outcome reason: .*outcome reason utf8_European[?][?].*_Katakana[?].*_Hiragana[?].* end', encoding=enc)
	
				# logFileContents:
				if enc == 'utf-8':
					self.assertGrep(outfile, expr=u'Text file contents: %s end'%self.utf8teststring, encoding=enc)
				elif enc == 'ascii': # ensure we have some suitable replacement chars
					self.assertGrep(outfile, expr='Text file contents: utf8_European[?][?].*_Katakana[?].*_Hiragana[?].* end', encoding=enc)
	