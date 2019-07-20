import os
from pysys.basetest import BaseTest
from pysys.baserunner import BaseRunner
from pysys.xml.descriptor import DescriptorLoader, TestDescriptor
from pysys.constants import PASSED

class MyTestClass(BaseTest):
	def execute(self):
		self.log.info('This is a custom test using: %s'%self.descriptor.file)
		self.addOutcome(PASSED)

class CustomDescriptorLoader(DescriptorLoader):

	def _handleSubDirectory(self, dir, subdirs, files, descriptors, parentDirDefaults, **kwargs):
		# can merge in defaults from parent dir if desired
		idprefix = '' if parentDirDefaults is None else parentDirDefaults.id
	
		if 'ace_descriptor.json' in files:
			descriptors.append(TestDescriptor(
				file=dir+'/ace_descriptor.json', 
				id=idprefix+os.path.basename(dir), 
				title=u"My ace test",
				groups=[u'ace-tests'], 
				modes=[u'MyMode1', u'MyMode2'],
				classname="MyTestClass",
				module=os.path.abspath(__file__.split('.')[0])
				))
			return True # don't look for PySys tests under this tree
		
		# ... alternatively	... this is an example of some descriptors that 
		# can exist alongside PySys tests
		for f in files:
			if f.endswith('.funky'):
				descriptors.append(TestDescriptor(
					file=dir+'/'+f, 
					id=idprefix+f.split('.')[0], # get the test id from the filename 
					title=u"My funky test",
					groups=[u'funky-tests'], 
					classname="MyTestClass",
					module=__file__.split('.')[0]
					))
		return False # continue to look for PySys tests
