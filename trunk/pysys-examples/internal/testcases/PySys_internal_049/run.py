from pysys.constants import *
from pysys.utils.filecopy import filecopy
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		exprList=[]
		exprList.append('(?P<direction>westlin|eastlin)')
		exprList.append('moon shines bright')
		exprList.append('my charmer')			
		self.assertOrderedGrep(file='file.txt', filedir=self.input, exprList=exprList, assertMessage='Do we know the direction?')
		self.log.info('Copying run.log for later verification')
		filecopy(os.path.join(self.output, 'run.log'), os.path.join(self.output, 'run.log.proc'))
		
	def validate(self):
		del self.outcome[:]
		self.assertGrep('run.log.proc', expr='Do we know the direction?')