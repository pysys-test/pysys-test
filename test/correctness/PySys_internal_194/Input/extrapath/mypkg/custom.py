import time, logging, sys, threading, os

from pysys.writer import BaseResultsWriter
from pysys.utils.logutils import stdoutPrint

log = logging.getLogger('pysys.writer')

class CustomWriter(BaseResultsWriter):
	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, runLogOutput=u'', **kwargs):
		stdoutPrint('CustomWriter.processResult: %s'%testObj)

	def isEnabled(self, record=False, **kwargs):
		return True
