import time, logging, sys, threading, os

from pysys.writer import BaseResultsWriter
from pysys.utils.logutils import stdoutPrint
from pysys.utils.pycompat import PY2

log = logging.getLogger('pysys.writer')

class CustomWriter(BaseResultsWriter):
	def setup(self, numTests=0, cycles=1, xargs=None, threads=0, testoutdir=u'', runner=None, **kwargs):
		sys.stdout.write('sys.stdout.write-CUSTOMWRITER-setup\n')
		stdoutPrint('stdoutPrint-CUSTOMWRITER-setup')
		
	def cleanup(self, **kwargs):
		sys.stdout.write('sys.stdout.write-CUSTOMWRITER-cleanup\n')
		stdoutPrint(u'stdoutPrint-CUSTOMWRITER-cleanup')

	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, runLogOutput=u'', **kwargs):
		sys.stdout.write('sys.stdout.write-CUSTOMWRITER-processResult\n')
		stdoutPrint(b'stdoutPrint-CUSTOMWRITER-processResult')
