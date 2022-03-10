from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = self.input+"/reader.py"
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = os.environ,
						  workingDir = self.output,
						  stdouterr = 'reader',
						  state=BACKGROUND)

		# write to the process stdin
		self.log.info("Writing to the process stdin")
		self.hprocess.write(b"The cat sat on the mat\n")
		self.wait(1.0) # just in case the reader was doing 
		self.writeProcess(self.hprocess, "No westlin winds and slaughtering guns")
		self.hprocess.write("In the temple of science there are many mansions ", addNewLine=False)
		self.writeProcess(self.hprocess, "and varied indeed are those that dwell therein ", addNewLine=False)
		self.hprocess.write("and the motives that have led them there", addNewLine=True, closeStdinAfterWrite=True)
		self.hprocess.write("should fail", addNewLine=True)

		# wait for the strings to be writen to sdtout
		self.waitForGrep("reader.out", expr=r"EOF")
			
	def validate(self):
		# validate against the reference file
		self.assertDiff("reader.out", "ref_reader.out")