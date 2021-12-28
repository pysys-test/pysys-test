__pysys_title__   = r""" Nested test""" 
	
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.config.descriptor import DescriptorLoader, TestDescriptor
import io, time

class PySysTest(BaseTest):
	def execute(self):
		loader = DescriptorLoader(project=self.project)
				
		if self.descriptorFile != 'CreateEmptyDescriptor':
			ext = '.py' if self.descriptorFile.startswith('Python') else '.xml'
			with io.open(self.descriptor.testDir+'/../'+self.descriptorFile+ext, 'rb') as inputfile:
				fileContents = inputfile.read()
		else:
			fileContents = None
			
		starttime = time.time()
		endtime  = starttime+float(self.testDurationSecs)
		iterations = 0
		checktime = True
		
		parentDirDefaults = self.project._defaultDirConfig# or self.DEFAULT_DESCRIPTOR
		
		while (not checktime) or time.time()<endtime:
			iterations += 1
			
			if fileContents is None:
				d = TestDescriptor('EmptyDescriptor.py', 'EmptyDescriptor.py')
			else:
				d = loader._parseTestDescriptor(self.descriptorFile+ext, parentDirDefaults=None, 
					# use this special undocumented fileContents= value to avoid use of disk to generate more stable and pure results
					fileContents=fileContents.replace(b'@TEST_ID@', b'Test%03d'%iterations))
			assert d
			
			checktime = iterations % 100 == 0

		self.log.info('%s descriptor load rate is: %f /sec', self.descriptorFile, (iterations)/(time.time()-starttime))

	def validate(self):
		self.addOutcome(INSPECT, 'See performance results')
