import os
from pysys.basetest import BaseTest
from pysys.baserunner import BaseRunner
from pysys.config.descriptor import DescriptorLoader, TestDescriptor
from pysys.constants import PASSED
from pysys.utils.fileutils import toLongPathSafe

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

			# also test what it looks like to do a lookaside and find tests in another directory e.g. under the source tree
			descriptors.append(TestDescriptor(
				file=toLongPathSafe(self.project.testRootDir+'/../someSrcLocation'), # use long path safe just to make sure this works
				output=toLongPathSafe(dir+'/Output/'+idprefix+os.path.basename(dir)), # use long path safe just to make sure this works
				id=idprefix+os.path.basename(dir)+'_FromSrcDir', 
				title=u"My ace test, actually located in source directory",
				classname="MyTestClass",
				modes=[u'MyModeForSrcFile'],
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
