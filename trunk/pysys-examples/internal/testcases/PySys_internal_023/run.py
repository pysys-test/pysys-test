from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/internal/utilities/scripts/reader.py" % self.project.root
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "3"],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "%s/reader.out" % self.output,
						  stderr = "%s/reader.err" % self.output,
						  state=BACKGROUND)
						 
		# write some lines into the process stdin
		while not self.hprocess.running():
			time.sleep(1)
		
		self.log.info("Writing to the process stdin")
		self.hprocess.write("The cat sat on the mat")
		self.hprocess.write("No westlin winds and slaughtering guns")
		self.hprocess.write("In the temple of science there are many mansions")
		self.wait(3)
	
	def validate(self):
		pass