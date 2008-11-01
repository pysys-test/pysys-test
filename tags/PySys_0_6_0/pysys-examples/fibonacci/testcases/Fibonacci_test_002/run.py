import os.path
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	'''Example PySys testcase.'''
	
	def execute(self):
		'''Override the BaseTest.execute method to perform the test execution.
		
		The execute method creates in memory the first ten entries of the 
		fibonacci series and writes the values to disk into the testcase 
		output directory. Validation of the series can then be performed 
		on the output file contents.
		
		'''
		fib = []
		fib.append(0)
		fib.append(1)
		
		self.log.info("Calculating fibonacci series with ten entries")
		for i in range(2, 10):
			fib.append(fib[i-1] + fib[i-2])

		self.log.info("Writting fibonacci series to test output subdirectory")
		f=open(os.path.join(self.output, 'fibonacci.txt'), 'w')
		for line in fib:
			f.write('%s\n' % line)
		f.close()


	def validate(self):
		'''Override the BaseTest.validate method to perform the test validation.
	
		Perform multiple validation steps on the output file containing the 
		calculated fibonacci series. This demonstrates how assertions build up 
		an outcome list, where the overall outcome of the test is based on a 
		precedence of the possible individual outcomes.

		'''
		# first validation diffs the output with the reference
		self.assertDiff('fibonacci.txt', 'ref_fibonacci.txt')

		# next validation looks for regexps in the output file
		self.assertGrep('fibonacci.txt', expr='34')
		self.assertGrep('fibonacci.txt', expr='55', contains=FALSE)

		# next validation looks for an ordered sequence of regexp
		self.assertOrderedGrep('fibonacci.txt', exprList=['0', '1', '1', '5'])

		# next validation looks for the number of lines matching a regexpr
		self.assertLineCount('fibonacci.txt', expr='[0-9]+', condition='==10')


      
