from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		with open(self.output+'/wait.py', 'w') as f:
			f.write('import time\ntime.sleep(5)\nwhile True: pass')
		p = self.startProcess(command=sys.executable,
						  arguments = [self.output+'/wait.py'],
						  environs = dict(os.environ),
						  stdout = "%s/test.out" % self.output,
						  stderr = "%s/test.err" % self.output,
						  state=BACKGROUND)
		pm = self.startProcessMonitor(p, interval=0.1, file='monitor.dat')
		pm2 = self.startProcessMonitor(p, interval=0.1, file=self.output+'/monitor-numproc.dat', numProcessors=10)
		assert pm.running()
		self.waitForSignal('monitor.dat', expr='.', condition='>=5')
		self.waitForSignal('monitor-numproc.dat', expr='.', condition='>=5')
		assert pm.running()
		self.stopProcessMonitor(pm)
		self.stopProcessMonitor(pm) # should silently do nothing
		p.stop()
		self.wait(1)
		self.stopProcessMonitor(pm2)
						  
		
	def validate(self):
		with open(self.output+'/monitor.dat') as f:
			f.readline()
			line = f.readline().strip() # ignore first line
		# ensure tab-delimited output has same number of items as header
		line = line.split('\t')
		self.log.info('Sample log line:   %s', line)
		self.assertThat('%d >= 4', len(line)) # 4 columns on unix, more on windows
		for i in range(len(line)):
			if i > 0: # apart from the first column, every header should be a valid float or int
				self.assertThat('float(%s) or True', repr(line[i]))