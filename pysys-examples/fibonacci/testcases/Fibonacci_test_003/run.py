from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		if self.mode in ['FibonacciMode1', 'FibonacciMode2']:
			# in a real application, the modes would have different implementations
			self.startProcess(
				command=sys.executable, # This program uses the python executable
				arguments=[self.input+'/fibonacci.py'],
				stdouterr=self.allocateUniqueStdOutErr('fibonacci'),
				state=FOREGROUND)
		else:
			raise Exception('Unknown mode: "%s"'%self.mode)
		
	def validate(self):
		# first validation diffs the output with the reference
		self.assertDiff('fibonacci.out', 'ref_fibonacci.out')

		# next validation looks for regexps in the output file
		self.assertGrep('fibonacci.out', expr='^34')
		self.assertGrep('fibonacci.out', expr='^55', contains=False)

		# next validation looks for an ordered sequence of regexp
		self.assertOrderedGrep('fibonacci.out', exprList=['0', '1', '1', '5'])

		# next validation looks for the number of lines matching a regexpr
		self.assertLineCount('fibonacci.out', expr='^[0-9]+', condition='==10')
