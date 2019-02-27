from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

# May need to increase this on fast machines/filesystems
# if no warnings are logged after validate() finishes.
NUM_FILES = 25000

class PySysTest(BaseTest):
	
	def execute(self):
		# Create a whole lot of output files 
		self.createFiles()
		
		# Delete all the output files in a background process,
		# this should still be running when validate() finishes.
		self.proc = ProcessWrapper(sys.executable, [os.path.join(self.input, "deleteFiles.py"), str(NUM_FILES), self.output], os.environ, self.output, BACKGROUND, 60, os.path.join(self.output, "stdout.log"), os.path.join(self.output, "stderr.log"))
		self.proc.start()
		
	def validate(self):
		# I don't like doing this but we are trying to provoke a
		# race condition, so give the delete script time to start.
		self.wait(0.5)

		# Test should pass unless an exception is thrown and not
		# ignored when scanning/cleaning the output directory. 
		self.addOutcome(PASSED)

	def createFiles(self):
		self.log.info("Creating %d files" % NUM_FILES)
		for i in range(1, NUM_FILES+1):
			with open(os.path.join(self.output, "%d.txt" % i), "w") as f:
				f.write(str(i))
				f.close()
		self.log.info("Completed creation of files")
