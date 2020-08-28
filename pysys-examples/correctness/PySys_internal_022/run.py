from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = self.project.pythonScriptsDir+"/counter.py"
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "20", "3"],
						  workingDir = self.output,
						  stdout = "%s/counter.out" % self.output,
						  stderr = "%s/counter.err" % self.output,
						  state=BACKGROUND)
		
		# check the process status
		self.initialstatus = self.hprocess.running()
		
		# wait for ten iterations and then stop the process
		self.waitForGrep('counter.out', expr='Count is 9')
		self.stopProcess(self.hprocess)
		
		# check the process status
		self.finalstatus = self.hprocess.running()
		
		# log what the process exit status is
		self.log.info("Exit status of the process is %d",  self.hprocess.exitStatus)

	
	def validate(self):
		# process running status should have been true to start
		self.assertTrue(self.initialstatus)
		
		# process running status should have been false on completion
		self.assertFalse(self.finalstatus)
	
		# check the sdtout of the process
		self.assertDiff('counter.out', 'ref_counter.out')
		
