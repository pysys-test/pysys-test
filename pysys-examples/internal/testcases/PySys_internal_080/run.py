from pysys.constants import *
from pysys.basetest import BaseTest
#from pysys.process.monitor import *

class PySysTest(BaseTest):

	def execute(self):
		p = self.startProcess(command=sys.executable,
						  arguments = [self.input+'/spinner.py'],
						  stdout = "%s/test.out" % self.output,
						  stderr = "%s/test.err" % self.output,
						  state=BACKGROUND)
		pm = self.startProcessMonitor(p, interval=0.1, file='monitor.tsv')
		pm2 = self.startProcessMonitor(p, interval=0.1, file=self.output+'/monitor-numproc.tsv', numProcessors=10)
		assert pm.running(), 'monitor is still running'
		self.waitForSignal('monitor.tsv', expr='.', condition='>=5', ignores=['#.*'])
		self.waitForSignal('monitor-numproc.tsv', expr='.', condition='>=5', ignores=['#.*'])
		assert pm.running(), 'monitor is still running'
		self.stopProcessMonitor(pm)
		pm.stop() # should silently do nothing
		self.stopProcessMonitor(pm) # should silently do nothing
		p.stop()
		self.wait(1) # keep process monitor running after it to check it doesn't cause an error
		self.stopProcessMonitor(pm2)
						  
		
	def validate(self):
		with open(self.output+'/monitor.tsv') as f:
			header = f.readline()
			f.readline() # ignore first line of results
			line = f.readline().strip() 
		# ensure tab-delimited output has same number of items as header
		line = line.split('\t')
		self.log.info('Sample log line:   %s', line)
		self.assertThat('%d >= 4', len(line)) # 4 columns on unix, more on windows
		for i in range(len(line)):
			if i > 0: # apart from the first column, every header should be a valid float or int
				self.assertThat('float(%s) or True', repr(line[i])) # would raise an exception if not a float