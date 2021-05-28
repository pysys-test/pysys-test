import pysys
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):
	def execute(self):
		# Log out all the project properties
		for propName, propValue in sorted(self.project.properties.items()):
			self.log.info('Project property %s=%r', propName, propValue)
		self.log.info('')

		# Example of using a project property for a username+password combination
		username, password = self.project.myCredentials.split(':')
		self.log.info('Using username=%s and password=%s', username, password)

		self.log.info('Using logConfigURL=%s', self.project.logConfigURL)

	def validate(self):
		# Demo of how to get the value of a property with a string value
		self.assertThat('len(appHome) > 0', appHome=self.project.appHome)
				
		# This one originally came from a .properties file
		self.assertThat('len(os_myThirdPartyLibraryDir) > 0', os_myThirdPartyLibraryDir__eval="self.project.os_myThirdPartyLibraryDir")

		# Demo of how to get the value of a property with a non-string value, and with a default in case not set in pysysproject.xml
		self.assertThat('myBoolProp is expected', myBoolProp__eval="self.project.getProperty('myBoolProp', default=True)", expected=True)
		self.assertThat('myListProp == expected', myListProp__eval="self.project.getProperty('myListProp', default=['a', 'b', 'c'])", 
			expected=['a', 'b', 'c'])
