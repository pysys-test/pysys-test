from pysys.exceptions import *
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.filecopy import filecopy 

class PySysTest(BaseTest):
	def execute(self):
		try:
			# in this one test we still use waitForSignal to check for compatibility
			# we also deliberately use the positional form of filedir in position 2 just to check we don't break this
			self.waitForSignal('input.log', self.input, expr='Foo', timeout=1, abortOnError=True, ignores=['line .s to be ignored'])
		except AbortExecution as e:
			self.log.info('%s [%s]' % (e.value, ','.join(e.callRecord)))

	def validate(self):
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Wait.*timed out.*\[.+run.py:11\]')
