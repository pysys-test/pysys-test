from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = self.project.pythonScriptsDir+"/counter.py"
	

		try:
			self.startProcess(command='./non-existent-process',
							  arguments=[],
							  state=FOREGROUND)
		except Exception as ex:
			self.addOutcome(PASSED, 'Got exception as expected: %s'%ex, override=True)
		else:
			self.abort('Expected exception from failed process start')
			
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "2", 3],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "counter.out",
						  stderr = "%s/counter.err" % self.output,
						  ignoreExitStatus=True,
						  state=FOREGROUND)
		
		# do a couple of wait for files
		self.waitForFile('counter.out', timeout=4)
		self.waitForFile('counter.err', timeout=4)
						  
		# do a couple of wait for signals in the files
		self.waitForGrep('counter.out', expr='Count is 1', timeout=4)
		self.waitForGrep('counter.err', expr='Process id of test executable', timeout=4)	

		
	def validate(self):
		# check the sdtout of the process
		self.assertDiff('counter.out', 'ref_counter.out')
		
		# check the stderr of the process
		self.assertGrep('counter.err', expr='Process id of test executable is %d' % self.hprocess.pid)
		
		# check the return status of the process
		self.assertTrue(self.hprocess.exitStatus == 3)
		
