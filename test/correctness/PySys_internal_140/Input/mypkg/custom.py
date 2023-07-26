import os
import pysys
from pysys.basetest import BaseTest
from pysys.baserunner import BaseRunner
from pysys.config.descriptor import DescriptorLoader, TestDescriptor
from pysys.constants import PASSED
import logging

class MyTestClass(BaseTest):
	def execute(self):
		self.log.info('This is a custom test using: %s'%self.descriptor.file)
		self.addOutcome(PASSED)

class CustomDescriptorLoaderPlugin(object):

	myJSONFilename = 'foo.json'
	"""
	Sample plugin property. 
	"""

	def setup(self, project, **kwargs):
		logging.getLogger('custom').info('CustomDescriptorLoaderPlugin constructor with myJSONFilename=%s', self.myJSONFilename)
		assert self.myJSONFilename != 'foo.json', 'ensure plugin property has been set'

		assert self.descriptorLoader, 'should have been set'
		assert self.project, 'should have been set'

	def addDescriptorsFromDirectory(self, dir, subdirs, files, parentDirDefaults, descriptors, **kwargs):
		logging.getLogger('custom').info('CustomDescriptorLoaderPlugin addDescriptorsFromDirectory: %s', dir)

		# can merge in defaults from parent dir if desired
		idprefix = '' if parentDirDefaults is None else parentDirDefaults.id
	
		if self.myJSONFilename in files:
			descriptors.append(TestDescriptor(
				file=dir+'/'+self.myJSONFilename, 
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
				d = TestDescriptor(
					file=dir+'/'+f, 
					id=idprefix+f.split('.')[0], # get the test id from the filename 
					title=u"My funky test",
					groups=[u'funky-tests'], 
					classname="MyTestClass",
					module=__file__.split('.')[0]
					)
				d.setId(d.id+'.suffix')
				descriptors.append(d)
		return False # continue to look for PySys tests
