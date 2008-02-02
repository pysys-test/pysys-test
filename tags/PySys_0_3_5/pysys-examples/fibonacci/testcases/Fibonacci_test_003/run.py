from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		self.startProcess(command=sys.executable,
						  arguments = ["%s/fibonacci.py" % self.input],
						  environs = os.environ,
						  workingDir = self.input,
						  stdout = "%s/fibonacci.out" % self.output,
						  stderr = "%s/fibonacci.err" % self.output,
						  state=FOREGROUND)

	def validate(self):
		# first validation diffs the output with the reference
		self.assertDiff('fibonacci.out', 'ref_fibonacci.out')

		# next validation looks for regexps in the output file
		self.assertGrep('fibonacci.out', expr='34')
		self.assertGrep('fibonacci.out', expr='55', contains=FALSE)

		# next validation looks for an ordered sequence of regexp
		self.assertOrderedGrep('fibonacci.out', exprList=['0', '1', '1', '5'])

		# next validation looks for the number of lines matching a regexpr
		self.assertLineCount('fibonacci.out', expr='^[0-9]+', condition='==10')

