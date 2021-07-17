import pysys
#from pysys.constants import *
from pysys.basetest import BaseTest

from pysys.xml.project import *
from pysys.xml.manual import *
from pysys.xml.descriptor import *

import pysys.xml.project

class PySysTest(BaseTest):
	def execute(self):
		assert TestDescriptor
		assert DescriptorLoader
		assert TestMode
		assert XMLManualTestStep
		assert Project
		
		self.assertThat('xmlgetinstance is selfproject', xmlgetinstance=Project.getInstance(), selfproject=self.project)
		self.assertThat('xmlproject is selfproject', xmlproject=pysys.xml.project.Project.getInstance(), selfproject=self.project)

		self.explicitImports()

	def explicitImports(self):
		from pysys.xml.project import Project
		from pysys.xml.descriptor import TestDescriptor
		from pysys.xml.manual import XMLManualTestStep

	def validate(self):
		pass
	