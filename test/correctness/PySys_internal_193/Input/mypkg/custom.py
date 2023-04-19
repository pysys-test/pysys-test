import os
import pysys
from pysys.basetest import BaseTest
from pysys.constants import PASSED

class MyTestClass(BaseTest):
	userdata2 = ['default']
	userdataInt = 0
	def execute(self):
		self.log.info('This is a custom test using: %s'%self.descriptor.file)
		self.log.info('User data: %s'%self.descriptor.userData)
		self.log.info('Test userdata1: %r'%self.userdata1)
		self.log.info('Test userdata2: %r'%self.userdata2)
		self.log.info('Test userdataInt: %r'%self.userdataInt)

		self.addOutcome(PASSED)
