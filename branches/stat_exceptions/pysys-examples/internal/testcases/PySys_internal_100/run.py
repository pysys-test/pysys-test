from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

NUM_FILES = 10000

class PySysTest(BaseTest):
	
	def execute(self):
		# Create a whole lot of output files 
		self.createFiles()
		
		# Delete all the output files in a background process,
		# this should still be running when validate() finishes.
		self.proc = ProcessWrapper(sys.executable, [os.path.join(self.input, "deleteFiles.py"), str(NUM_FILES), self.output], os.environ, self.output, BACKGROUND, 60, os.path.join(self.output, "stdout.log"), os.path.join(self.output, "stderr.log"))
		self.proc.start()
		
	def validate(self):
		# Test should pass unless an exception is thrown and not
		# ignored when scanning/cleaning the output directory. 
		self.addOutcome(PASSED)

	def createFiles(self):
		log.info("Creating %d files..." % NUM_FILES)
		for i in range(1, NUM_FILES+1):
			with open(os.path.join(self.output, "%d.txt" % i), "w") as f:
				f.write(str(i))
				f.close()
		log.info("   ...done")
