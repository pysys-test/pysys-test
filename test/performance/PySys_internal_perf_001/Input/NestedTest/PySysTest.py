__pysys_title__   = r""" Nested test""" 
#                        ================================================================================

__pysys_purpose__ = r""" 
	
	""" 
	
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.config.descriptor import DescriptorLoader
import io, time

class PySysTest(BaseTest):
	testsPerLoader = 0 # set by parent
	
	def execute(self):
		loader = DescriptorLoader(project=self.project)
		
		for i in range(int(self.testsPerLoader)):
			d = self.mkdir(self.output+'/rootdir/subdir1/subdir2/Test_%03d'%(i+1))

			ext = '.py' if self.descriptorFile.startswith('Python') else '.xml'
			with io.open(self.descriptor.testDir+'/../'+self.descriptorFile+ext, encoding='utf-8') as inputfile:
				with io.open(d+'/pysystest'+ext, 'w', encoding='utf-8') as f:
					f.write(inputfile.read().replace('@TEST_ID@', 'Test%03d'%i))

		starttime = time.time()
		endtime  = starttime+float(self.testDurationSecs)
		iterations = 0
		while time.time()<endtime:
			iterations += 1
			descriptors = loader.loadDescriptors(self.output+'/rootdir')
			assert descriptors, descriptors

		self.log.info('%s descriptor load rate is: %f /sec (%d iterations)', self.descriptorFile, (iterations*int(self.testsPerLoader))/(time.time()-starttime), iterations)
		
		self.addOutcome(INSPECT, 'See performance results')

	def validate(self):
		pass 
