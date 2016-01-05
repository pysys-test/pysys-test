from pysys.exceptions import *
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.filecopy import filecopy 

class PySysTest(BaseTest):
	def execute(self):
		try:
			self.waitForSignal('input.log', filedir=self.input, expr='Foo', timeout=1, abortOnError=True)		
		except AbortExecution, e:
			self.log.info('%s [%s]' % (e.value, ','.join(e.callRecord)))


	def validate(self):
                filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
                del self.outcome[:]
                self.assertGrep('run.log.proc', expr='Wait.*timed out.*\[run.py:9\]')
