# -*- coding: latin-1 -*-

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
import os, sys, math, shutil, glob, re
import xml.dom.minidom
from pysys.utils.pycompat import PY2

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		# make testRootDir and working dir be different
		os.rename(self.output+'/test/pysysproject.xml', self.output+'/pysysproject.xml')

		runPySys(self, 'pysys', ['run', '--progress', '-o', self.output+'/myoutdir', '--record'], workingDir='test', ignoreExitStatus=True)
		self.logFileContents('myoutdir/NestedFail/run.log', maxLines=0)
		#self.assertGrep('pysys.out', expr='Test final outcome: .*(PASSED|NOT VERIFIED)', abortOnError=True)
			
	def validate(self):
		self.assertGrep('pysys.err', expr='.+', contains=False)


		# XML spec says Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
		# ignore reserved unicode surrogate character range D800-DFFF which Python doesn't handle; > x10FFFF is not valid unicode
		# explore just before and just after each set of chars )but remove \n and \r, tested elsewhere)
		# nb: ! precedes each charcater that should be removed
		controlchars = u'!\x00 !\x01 tab\x09tab !\x10 !\x11 !\x0B !\x0C !\x0E !\x19 space\x20space BMP: \uD7FF \uE000 \uFFFD !\uFFFE !\uFFFF SMP: \U00010000 \U00010001 \U0010FFFF'
		self.assertGrep('myoutdir/NestedFail/run.log', expr=u'Log with control characters: %s end'%controlchars, encoding='utf-8')

		self.assertGrep('myoutdir/NestedFail/run.log', expr=u'Test outcome reason: .*Outcome with control characters: %s end'%
			u'! ! tab tab ! ! ! ! ! ! space\x20space BMP: \uD7FF \uE000 \uFFFD !\uFFFE !\uFFFF SMP: \U00010000 \U00010001 \U0010FFFF',
			encoding='utf-8')


		escapedcontrolchars = re.escape(u'!? !? tab\x09tab !? !? !? !? !? !? space\x20space BMP: \uD7FF \uE000 \uFFFD !? !?')
		smpchars = re.escape(u' SMP: \U00010000 \U00010001 \U0010FFFF')
		if PY2:
			# python 2 has less good support for supplementary multilingual plane characters, 
			# though some builds of python (e.g. on Travis) seem to work ok. 
			#check we get either correct characters, or that it degrades gracefully with some substitution chars
			smpchars = u'('+smpchars+u'|'+re.escape(u' SMP: ?? ?? ??')+u')'
		escapedcontrolchars += smpchars
		self.logFileContents('junit-report/TEST-NestedFail.xml', encoding='utf-8', includes=['Log with control characters:.*'])
		self.assertGrep('junit-report/TEST-NestedFail.xml', expr=u'Log with control characters: .+ end', encoding='utf-8')
		self.assertGrep('junit-report/TEST-NestedFail.xml', expr=u'Log with control characters: %s end'%escapedcontrolchars, encoding='utf-8')
		
		# given the above check all we need to verify here is that the outcome reason is included
		self.assertGrep('junit-report/TEST-NestedFail.xml', expr=u'<failure message="FAILED: Outcome with control characters: .+ end"', encoding='utf-8')
		self.assertGrep('testsummary.xml', expr=u'<outcomeReason>Outcome with control characters: .+ end', encoding='utf-8')
		
		# ensure we're generating valid parseable XML, i.e. not getting exceptions from these
		doc = xml.dom.minidom.parse(self.output+'/junit-report/TEST-NestedFail.xml')
		try:
			stdout = doc.getElementsByTagName('system-out')[0].firstChild.data
		finally:
			doc.unlink()
		xml.dom.minidom.parse(self.output+'/testsummary.xml').unlink()
