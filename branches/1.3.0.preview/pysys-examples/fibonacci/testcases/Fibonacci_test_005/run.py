import time, shutil, os
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import PerformanceUnit

class PySysTest(BaseTest):
	'''Example PySys testcase.'''
	
	def execute(self):
		'''Override the BaseTest.execute method to perform the test execution.
		
		'''
		shutil.copyfile(self.input+'/fib.py', self.output+'/fib.py')
		# For demonstration purposes we will run for a fixed time period, 
		# just to ensure we generate sensible results regardless of the hardware 
		# we're running on
		
		self.startProcess(sys.executable, arguments=[self.output+'/fib.py'], environs=os.environ,
			stdout='fib.out', stderr='fib.err', ignoreExitStatus=False, abortOnError=True)
		
	def validate(self):
		'''Override the BaseTest.validate method to perform the test validation.
		
		This is the best place to record performance results. 
	
		'''
		iterations, calctime = self.getExprFromFile('fib.out', '([\d]+) calculations in ([\d.]+) seconds', groups=[1, 2])
		
		# where possible, report a "rate" rather than total time
		self.reportPerformanceResult(int(iterations)/float(calctime), 'Fibonacci sequence calculation rate', '/s', resultDetails=[('mode','python_fibonacci')])
		
		# an example showing how to report time when it's needed (e.g. for latency calculations)
		self.reportPerformanceResult(calctime, 'Fibonacci sequence calculation time', 's')
		
		# show how to report using custom units
		self.reportPerformanceResult(int(iterations)/float(calctime)/1000, 'Fibonacci sequence calculation rate with different units', unit=PerformanceUnit('kilo_fibonacci/s', biggerIsBetter=True))
