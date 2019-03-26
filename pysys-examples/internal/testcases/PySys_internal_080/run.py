from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.monitor import *
from pysys.utils.pycompat import openfile

class PySysTest(BaseTest):

	def execute(self):
		p = self.startProcess(command=sys.executable,
						  arguments = [self.input+'/spinner.py'],
						  stdout = "%s/test.out" % self.output,
						  stderr = "%s/test.err" % self.output,
						  state=BACKGROUND)
						  
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		childtest = runPySys(self, 'pysys', ['run', '-o', self.output+'/myoutdir', '-X', 'pidToMonitor=%d'%p.pid], 
			state=BACKGROUND, workingDir=self.input+'/nestedtests')

		pm = self.startProcessMonitor(p, interval=0.1, file='monitor-default.tsv')
		pm2 = self.startProcessMonitor(p, interval=0.1, file=self.output+'/monitor-numproc.tsv', numProcessors='10')

		# test all supported stats, and also use of stream rather than filename
		filehandle = openfile(self.output+'/monitor-all.tsv', 'w', encoding='utf-8')
		self.addCleanupFunction(lambda: filehandle.close())
		pm_all = self.startProcessMonitor(p, interval=0.1,handlers=[
			TabSeparatedFileHandler(file=filehandle, columns=[
				ProcessMonitorKey.DATE_TIME,
				ProcessMonitorKey.SAMPLE,
				ProcessMonitorKey.CPU_CORE_UTILIZATION,
				ProcessMonitorKey.CPU_TOTAL_UTILIZATION,
				ProcessMonitorKey.MEMORY_RESIDENT_KB,
				ProcessMonitorKey.MEMORY_VIRTUAL_KB,
				ProcessMonitorKey.MEMORY_PRIVATE_KB,
				ProcessMonitorKey.THREADS,
				ProcessMonitorKey.KERNEL_HANDLES,
			])
		])

		pidmonitor = self.startProcessMonitor(p.pid, interval=0.1, file=self.output+'/monitor-pid.tsv')

		assert pm.running(), 'monitor is still running'
		self.waitForSignal('monitor-default.tsv', expr='.', condition='>=5', ignores=['#.*'])
		self.waitForSignal('monitor-numproc.tsv', expr='.', condition='>=5', ignores=['#.*'])
		self.waitForSignal('monitor-pid.tsv', expr='.', condition='>=5', ignores=['#.*'])
		self.waitForSignal('monitor-all.tsv', expr='.', condition='>=5', ignores=['#.*'])
		assert pm.running(), 'monitor is still running'
		assert pidmonitor.running(), 'pid monitor is still running'
		self.stopProcessMonitor(pidmonitor)

		self.waitProcess(childtest, timeout=60)
		self.assertTrue(childtest.exitStatus==0, assertMessage='nested pysys test passed')

		self.stopProcessMonitor(pm)
		pm.stop() # should silently do nothing
		self.stopProcessMonitor(pm) # should silently do nothing
		p.stop()
		self.wait(1) # keep process monitor running after it to check it doesn't cause an error
		self.stopProcessMonitor(pm2)
						  
		
	def validate(self):
		self.logFileContents('monitor-default.tsv')
		self.logFileContents('monitor-numproc.tsv')
		self.logFileContents('monitor-all.tsv')
		self.logFileContents('myoutdir/NestedTest/monitor-legacy.tsv')

		with open(self.output+'/myoutdir/NestedTest/monitor-legacy.tsv') as f:
			header = f.readline()
			f.readline() # ignore first line of results
			line = f.readline().strip() 
		# ensure tab-delimited output has same number of items as header
		line = line.split('\t')
		self.log.info('Sample legacy log line:   %s', line)
		if IS_WINDOWS:
			self.assertThat('%d == 7', len(line)) 
		else:
			self.assertThat('%d == 4', len(line)) 
		self.assertGrep('myoutdir/NestedTest/monitor-legacy.tsv', expr='#.*', contains=False) # no header line
		self.log.info('')
		
		with open(self.output+'/monitor-default.tsv') as f:
			header = f.readline()
			self.assertTrue(header.startswith('#')) 
			f.readline() # ignore first line of results
			line = f.readline().strip() 
		# ensure tab-delimited output has same number of items as header
		line = line.split('\t')
		self.log.info('Sample log line:   %s', line)
		self.assertThat('%d == %d', len(line), len(header.split('\t'))) # same number of items in header line as normal lines
		for i in range(len(line)):
			if i > 0: # apart from the first column, every header should be a valid float or int
				try:
					float(line[i])
				except Exception:
					self.addOutcome(FAILED, 'monitor-default.tsv sample line [%d] is not a number: "%s"'%line[i])

		with open(self.output+'/monitor-all.tsv') as f:
			header = f.readline()
			self.assertTrue(header.startswith('#')) 
			f.readline() # ignore first line of results
			line = f.readline().strip() 
		# ensure tab-delimited output has same number of items as header
		line = line.split('\t')
		self.log.info('Sample log line:   %s', line)
		self.assertThat('%d == %d', len(line), len(header.split('\t'))) # same number of items in header line as normal lines
		for i in range(len(line)):
			if i > 0: # apart from the first column, every header should be a valid float or int
				try:
					float(line[i])
				except Exception:
					self.addOutcome(FAILED, 'monitor-default.tsv sample line [%d] is not a number: "%s"'%(i, line[i]))
		
		# check files have at least some valid (non -1 ) values
		self.assertGrep('monitor-default.tsv', expr='\t[0-9]+')
		self.assertGrep('monitor-pid.tsv', expr='\t[0-9]+')
		self.assertGrep('myoutdir/NestedTest/monitor-legacy.tsv', expr='\t[0-9]+')
		
		# should be nothing where we couldn't get the data
		self.assertGrep('myoutdir/NestedTest/monitor-legacy.tsv', expr='\t-1', contains=False)
		self.assertGrep('myoutdir/NestedTest/monitor-legacy.tsv', expr=r'^\d\d/\d\d/\d\d \d\d:\d\d:\d\d\t')
