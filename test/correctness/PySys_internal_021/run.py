from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = self.project.pythonScriptsDir+"/counter.py"
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "10", "2"],
						  workingDir = self.output,
						  stdouterr = "counter",
						  state=BACKGROUND)
		
		# display name should be set based on stdouterr and executable
		self.assertThat('re.match("python.*<counter>", %s)', repr(self.hprocess.displayName))
		
		# check the process status
		self.initialstatus = self.hprocess.running()
		
		# wait for the process to complete (after 10 loops)
		self.waitProcess(self.hprocess, timeout=10)
		self.hprocess.wait(timeout=15) # to to prove this method behaves the same as the above
		
		# check the process status
		self.finalstatus = self.hprocess.running()
		
		
	def validate(self):
		# process running status should have been true to start
		self.assertTrue(self.initialstatus)
		
		# process running status should have been false on completion
		self.assertFalse(self.finalstatus)
	
		# check the sdtout of the process
		self.assertDiff('counter.out', 'ref_counter.out')
		
		# check the return status of the process
		self.assertTrue(self.hprocess.exitStatus == 2)
