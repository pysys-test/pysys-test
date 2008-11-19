from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper

class PySysTest(BaseTest):
	id1 = -1
	id2 = -2
	matches1 = None

	def execute(self):
		script = "%s/testscript.py" % self.input
	
		self.hprocess = self.startProcess(command=sys.executable,
						  arguments = [script],
						  environs = os.environ,
						  workingDir = self.output,
						  stdout = "%s/testscript.out" % self.output,
						  stderr = "%s/testscript.err" % self.output,
						  state=BACKGROUND)
						  	
		# wait for the first unique id signal
		matches = self.waitForSignal("testscript.out", expr="The first unique id is (?P<id1>\d+).*$", condition="==1", timeout=10)
		
		# grab the id from the match object
		try: self.id1 = int(matches[0].group('id1'))
		except: pass
		self.log.info("The first id is %d" % self.id1)
			
		# wait for the second unique id signal
		matches = self.waitForSignal("testscript.out", expr="The second unique id is (?P<id2>\d+).*$", condition=">=2", timeout=10)
		
		# grab the id from the match object
		try: self.id2 = int(matches[1].group('id2'))
		except: pass
		self.log.info("The second id is %d" % self.id2)

		# wait for a match that does not occur
		self.matches1 = self.waitForSignal("testscript.out", expr="This wont match", condition=">=2", timeout=2)

		# do a wa it on a file that does not exist
		self.waitForSignal("foobar.out", expr="This wont match", condition=">=2", timeout=2)

				
	def validate(self):
		self.assertTrue(int(self.id1) == 1287998)
		self.assertTrue(int(self.id2) == 6754322)
		self.assertTrue(self.matches1 == [])
