from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = self.project.pythonScriptsDir+"/reader.py"
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script, "3"],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "%s/reader.out" % self.output,
						  stderr = "%s/reader.err" % self.output,
						  state=BACKGROUND)

		# write to the process stdin
		self.log.info("Writing to the process stdin")
		self.hprocess.write(b"The cat sat on the mat\n")
		self.writeProcess(self.hprocess, "No westlin winds and slaughtering guns")
		self.hprocess.write(u"In the temple of science there are many mansions ", addNewLine=FALSE)
		self.writeProcess(self.hprocess, u"and varied indeed are those that dwell therein ", addNewLine=False)
		self.hprocess.write("and the motives that have led them there", addNewLine=TRUE)

		# wait for the strings to be writen to sdtout
		self.waitForGrep("reader.out", expr="Line \(2\)", timeout=5)
			
	def validate(self):
		# validate against the reference file
		self.assertDiff("reader.out", "ref_reader.out")