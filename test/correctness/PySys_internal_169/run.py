import pysys

from pysys.constants import *
assert Project # check it's imported after each one

from pysys.basetest import BaseTest

from pysys.xml.project import *
assert Project # check it's imported after each one

from pysys.xml.manual import *
assert Project # check it's imported after each one

from pysys.xml.descriptor import *
assert Project # check it's imported after each one

import pysys.xml.project

class PySysTest(BaseTest):
	def execute(self):
		assert TestDescriptor
		assert DescriptorLoader
		assert TestMode
		assert XMLManualTestStep
		assert Project
		
		self.assertThat('xmlproject is self.project', xmlproject=pysys.xml.project.Project.getInstance(), project=self.project)
		self.assertThat('xmlgetinstance is self.project', xmlgetinstance=Project.getInstance(), project=self.project)

		self.explicitImports()

	def explicitImports(self):
		from pysys.xml.project import Project
		from pysys.xml.descriptor import TestDescriptor
		from pysys.xml.manual import XMLManualTestStep

	def validate(self):
		pass
	