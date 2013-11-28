from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	'''Example PySys testcase.'''

	def execute(self):
		'''Override the BaseTest.execute method to perform the test execution.
		
		The execute method creates in memory the first ten entries of the 
		fibonacci series. 
		
		'''
		self.fib = []
		self.fib.append(0)
		self.fib.append(1)

		self.log.info("Calculating fibonacci series with ten entries")
		for i in range(2, 10):
			self.fib.append(self.fib[i-1] + self.fib[i-2])


	def validate(self):
		'''Override the BaseTest.validate method to perform the test validation.
	
		Check that the tenth entry of the fibonnaci series is equal to 14

		'''
		self.log.info("Performing test validation")
		self.log.info("Checking the tenth entry of the fibonacci series = 34")
		self.assertTrue(self.fib[9] == 34)
		
