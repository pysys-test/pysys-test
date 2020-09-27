import pysys

class MyTest(pysys.basetest.BaseTest):
	def execute(self):
		self.assertThat('False') # deliberate failure to exercise callrecord handling and make sure it doesn't throw
		self.addOutcome(pysys.constants.PASSED, override=True)
		self.assertGrep('run.log', r'\[mytest.py:[0-9]+') # check we extracted the call record correctly from this file