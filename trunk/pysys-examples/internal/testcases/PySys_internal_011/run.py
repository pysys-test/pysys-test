from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):

	def execute(self):
		script = "%s/testscript.py" % self.input
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "%s/testscript.out" % self.output,
						  stderr = "%s/testscript.err" % self.output,
						  state=BACKGROUND)
						  	
		# wait for the process to complete (after 10 loops)
		matches = self.waitForSignal("testscript.out", expr="The unique id of (?P<id>\d+) is this", condition="==1", timeout=10)
		
		# grab the id from the match object
		if matches: 
			self.token = matches.group('id')
			self.log.info("The id was seen as %s " % self.token)
		
	def validate(self):
		self.assertTrue(int(self.token) == 1287998)