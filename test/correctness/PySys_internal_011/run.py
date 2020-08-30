from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.process.helper import ProcessWrapper
import pysys

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
		matches = self.waitForGrep("testscript.out", expr="The first unique id is (?P<id1>\d+).*$", condition="==1", timeout=10)
		
		# grab the id from the match object
		try: self.id1 = int(matches[0].group('id1'))
		except: pass
		self.log.info("The first id is %d" % self.id1)
			
		# wait for the second unique id signal
		matches = self.waitForGrep("testscript.out", expr="The second unique id is (?P<id2>\d+).*$", condition=">=2", timeout=10)
		
		# grab the id from the match object
		try: self.id2 = int(matches[1].group('id2'))
		except: pass
		self.log.info("The second id is %d" % self.id2)

		if self.getOutcome() not in [PASSED,NOTVERIFIED]: self.abort(FAILED, 'expected passed outcome but got: %s %s'%(self.getOutcome(), self.getOutcomeReason()))

		# wait for a match that does not occur
		aborted=False
		try:
			self.matches1 = self.waitForGrep("testscript.out", expr="This wont match", condition=">=2", timeout=2, abortOnError=True)
		except Exception as e:
			self.log.info('Got expected abort %s', sys.exc_info()[0], exc_info=1)
			aborted = True
		if not aborted: self.abort(FAILED, 'test should have aborted')
			
		# do a wa it on a file that does not exist
		aborted=False
		try:
			self.waitForGrep("foobar.out", expr="This wont match", condition=">=2", timeout=2, abortOnError=True)
		except Exception as e:
			self.log.info('Got expected abort %s', sys.exc_info()[0], exc_info=1)
			aborted = True
		if not aborted: self.abort(FAILED, 'test should have aborted')

		# test with mappers
		matches = self.waitForGrep("testscript.out", expr=".*unique id.*", condition=">0", mappers=[
			pysys.mappers.IncludeLinesBetween('The second unique id'),
			])[0].group()
		self.assertThat('actual == expected', actual=matches, expected='The second unique id is 098765', testing='waitForGrep with mappers')

		# this is a convenient place to test the same functionality in getExprFromFile
		matches = self.getExprFromFile("testscript.out", expr=".*unique id.*",  mappers=[
			pysys.mappers.IncludeLinesBetween('The second unique id'),
			])
		self.assertThat('actual == expected', actual=matches, expected='The second unique id is 098765', testing='getExprFromFile with mappers')

				
	def validate(self):
		self.assertTrue(int(self.id1) == 1287998)
		self.assertTrue(int(self.id2) == 6754322)
