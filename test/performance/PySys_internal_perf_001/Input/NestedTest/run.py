from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.exceptions import *
from pysys.xml.descriptor import DescriptorLoader
import io, time

SMALL_DESCRIPTOR_TEMPLATE = u"""<?xml version="1.0" encoding="utf-8"?>
<pysystest>
  <description> 
    <title>My testcase {id}</title>
    <purpose>My purpose</purpose>
  </description>
</pysystest>
"""

LARGE_DESCRIPTOR_TEMPLATE = u"""<?xml version="1.0" encoding="utf-8"?>
<pysystest>
  <description> 
    <title>My testcase {id}</title>
    <purpose><![CDATA[
Yes this is one purposeful test, oh yeah
]]></purpose>
  </description>

  <classification>
    <groups>
      <group>group-1</group>
      <group>group-2</group>
    </groups>
    <modes>
		<mode>MyMode1</mode>
		<mode>MyMode2</mode>
    </modes>
  </classification>

  <skipped reason="Skip reason"/>
  <execution-order hint="100"/> 
 
  <data>
    <class name="PySysTest" module="run"/>
    <input path="MyInput"/>
    <output path="MyOutput"/>
    <reference path="MyReference"/>
  </data>
  
  <traceability>
    <requirements>
      <requirement id="requirement1"/>     
      <requirement id="requirement2"/>     
    </requirements>
  </traceability>
</pysystest>
"""

class PySysTest(BaseTest):
	testDurationSecs = '1.0'
	testsPerLoader = '200'

	def execute(self):
		loader = DescriptorLoader(project=self.project)
		
		for i in range(int(self.testsPerLoader)):
			d = self.mkdir(self.output+'/rootdir-small/subdir1/subdir2/Test_%03d'%(i+1))

			with io.open(d+'/pysystest.xml', 'w', encoding='utf-8') as f:
				f.write(SMALL_DESCRIPTOR_TEMPLATE.format(id=i))

			d = self.mkdir(self.output+'/rootdir-large/subdir1/subdir2/Test_%03d'%(i+1))

			with io.open(d+'/pysystest.xml', 'w', encoding='utf-8') as f:
				f.write(LARGE_DESCRIPTOR_TEMPLATE.format(id=i))
		
		for subtest in ['large', 'small']:
		
			starttime = time.time()
			endtime  = starttime+float(self.testDurationSecs)
			iterations = 0
			while time.time()<endtime:
				iterations += 1
				descriptors = loader.loadDescriptors(self.output+'/rootdir-%s'%subtest)
				assert descriptors, descriptors

			self.log.info('%s descriptor load rate is: %f', subtest, (iterations*int(self.testsPerLoader))/(time.time()-starttime))
		self.addOutcome(INSPECT, 'See performance results')

	def validate(self):
		pass 
