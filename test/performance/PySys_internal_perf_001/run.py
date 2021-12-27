from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 
import pysys
import shutil

class PySysTest(BaseTest):

	testDurationSecs = 4.0

	def execute(self):
		
		self.copy(self.input, self.output+'/test')
		try:
			self.pysys.pysys('pysys', ['run', '-XtestDurationSecs=%s'%self.testDurationSecs], defaultproject=True, workingDir='test')
		finally:
			self.logFileContents('pysys.err')

	def validate(self):
		self.addOutcome(PASSED, '')
		resultDetails = {'PythonVersion':'%s.%s'%sys.version_info[0:2], 'PySysVersion':pysys.__version__, 'DurationSecs':self.testDurationSecs}
		
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'small descriptor load rate is: (.+)'), 
			'DescriptorLoader parse rate for XML small descriptors', 
			unit='/s', 
			resultDetails=resultDetails
			)
		self.reportPerformanceResult(
			self.getExprFromFile('pysys.out', 'large descriptor load rate is: (.+)'), 
			'DescriptorLoader parse rate for XML large descriptors', 
			unit='/s', 
			resultDetails=resultDetails
			)
