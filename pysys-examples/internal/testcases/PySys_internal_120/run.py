from pysys import stdoutHandler
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.constants import Project 

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	inputs = ['no-help', 'empty-help', 'starts-with-paragraph', 'starts-with-option', 'starts-with-heading']

	def execute(self):
		
		processes = []
		for i in self.inputs:
			processes.append(runPySys(self, i, ['run', '--help'], projectfile=self.input+'/'+i+'.xml', state=BACKGROUND))
		for p in processes:
			p.wait(timeout=60)
			assert p.exitStatus == 0, p

	def validate(self):
		self.logFileContents('starts-with-paragraph.out', tail=True)
		standardlines = len(self.getExprFromFile('no-help.out', expr='$', encoding='ascii', returnAll=True))
		class FilterByLineNumber:
			def __init__(self, lineNumberCondition):
				self.lineNumberCondition=lineNumberCondition
				self.__currentline = 0
			def __call__(self, line):
				self.__currentline += 1
				if eval(str(self.__currentline-1)+self.lineNumberCondition): return line
				return None
		
		for i in self.inputs:
			# strip out to just include the project help
			self.copy(i+'.out', 'projecthelp-'+i+'.out', mappers=[FilterByLineNumber('>= %s'%standardlines)
			])
			self.assertDiff('projecthelp-'+i+'.out')
		
		
		
		return
		# mostly checked by nested testcase, but also:
		self.assertGrep('pysys.out', expr='projectbool=True')
		self.assertGrep('pysys.out', expr='projectbooloverride=False')
		self.assertGrep('pysys.out', expr='booldeftrue=True')
		self.assertGrep('pysys.out', expr='booldeffalse=False')
		self.assertGrep('pysys.out', expr='cmdlineoverride=True')
		