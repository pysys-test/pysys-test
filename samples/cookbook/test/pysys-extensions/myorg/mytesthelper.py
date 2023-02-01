import sys
import logging

import pysys.basetest, pysys.mappers

class CookbookSampleHelper:
	""" A mix-in class providing functionality related to (something) in a test field called ``self.cookbook``. 

	To use this just inherit from it in your test, but be sure to leave the BaseTest as the last class, for example::

		from myorg.mytesthelper import MyTestHelper
		class PySysTest(MyTestHelper, pysys.basetest.BaseTest):
	
	This paradigm is the ideal way to reuse logic across your tests in a way that is modular, safe and encapsulated. 

	The functionality can be enabled just for the individual tests that need it, and any number of helpers can be 
	composed together in a risk-free way - without the multiple inheritance complications and danger of namespace 
	method/field name collisons you'd get if using multiple custom BaseTest subclasses to reuse your logic. 

	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs) # MUST start by calling super implementations
		self.cookbook = CookbookSampleHelper.CookbookSampleHelperImpl(self)
		""" Provides access to a set of helper methods for (something). """
		
	HELPER_MIXIN_FIELD_NAME = 'cookbook' # Informs PySys that this class adds a field of this name to the test class
	# NB: Do NOT add ANY extra methods/fields to the helper itself - all functionality must be safely encapsulated within the nested Impl class. 

	class CookbookSampleHelperImpl(object):
		def __init__(self, testObj: pysys.basetest.BaseTest):
			self.owner = testObj
			self.log = logging.getLogger('pysys.myorg.CookbookSampleHelper')
			# NB: could call self.owner.addCleanupFunction() if any standard cleanup logic is required. 

			self.log = logging.getLogger('pysys.myorg.MyTestPlugin')

			# Configuration items for this helper can be specified in project configuration properties:
			self.log.info('CookbookSampleHelper created; myPluginProperty=%r', self.owner.project.getProperty('CookbookSampleHelper.myPluginProperty', 12345))
			self.log.info('')

			# There is no standard cleanup() method, so do this if you need to execute something on cleanup for every test that uses this helper:
			testObj.addCleanupFunction(self.__myPluginCleanup)
		
		def __myPluginCleanup(self):
			pass
			# This would be a good place to perform a graceful shutdown of any processes started by this plugin, 
			# in case you want to check graceful shutdown works, or if it's needed to get code coverage results (any 
			# remaining processes are automatically killed later, so no need to worry about killing processes here)

		# An example of providing a method that can be accessed from each test
		def getPythonVersion(self):
			"""
			Example of a method that can be called by individual tests using this plugin. 
			"""
			self.owner.startProcess(pysys.constants.PYTHON_EXE, arguments=['--version'], stdouterr='CookbookSampleHelper.pythonVersion')
			return self.owner.waitForGrep('CookbookSampleHelper.pythonVersion.out', '(?P<output>.+)')['output'].strip()

		# A common pattern is to create a helper method that you always call from your `BaseTest.validate()`
		# That approach allows you to later customize the logic by changing just one single place, and also to omit 
		# it for specific tests where it is not wanted. 
		def checkLog(self, logfile='my_server.out', ignores=[]):
			"""
			Asserts that the specified log file does not contain any errors. 
			"""
			self.assertGrep(logfile, ' (ERROR|FATAL) .*', contains=False, 
				ignores=ignores or ['ERROR .*Expected error'])

		# This is convenient way to allow access to the owner's methods and fields as if they were on self; e.g. "self.assertGrep"
		def __getattr__(self, name): return getattr(self.owner, name)
