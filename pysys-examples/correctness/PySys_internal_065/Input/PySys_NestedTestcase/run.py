from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *

class PySysTest(BaseTest):
	def execute(self):
		self.reportPerformanceResult(123, 'Sample small integer performance result', 's', resultDetails=[('someResultDetail','value,yesitis')])
		self.reportPerformanceResult(1234, 'Sample large integer performance result', 's', resultDetails=[('someResultDetail','value,yesitis')])
		self.reportPerformanceResult(0.012341, 'Sample float performance result', '/s')
		self.reportPerformanceResult('0.0123415', 'Sample string float performance result', '/s')

	def validate(self):
		pass 
