# Sample pysystest.py file defining a test (part of the "cookbook" sample). 

# Test titles should be concise but give a clear idea of what is in scope for this testcase. 
#
# Good titles make it easy to find the test you need even when you have 100s/1000s of tests. 
# Tests can be sorted by title so try to use common prefixes (e.g. ``Category - Title``) to group related tests 
# together, and run ``pysys print -s=title`` to see how your title looks alongside the existing titles. 
#
# Titles need to be human readable at-a-glance, so don't put ids (e.g. bug tracking numbers) in the title; 
# the "purpose" or "traceability_ids" are a better place for those details. 
#
__pysys_title__   = r""" My foobar tool - Argument parsing success and error cases """
#                        ===============================================================================
# The underlined line length guide comment (above) discourages excessively long titles.

# The purpose is a good place for a fuller description of what is in and out of scope for this particular testcase.
__pysys_purpose__ = r""" The purpose of this test is to check that 
	argument parsing addresses these criteria:
		- Correctness
		- Clear error messages
	"""

# It's useful to keep track of who created each test and/or made subsequent changes so you know who can help if you 
# need help debugging a problem. 
__pysys_authors__ = "userid1, userid2, Joe Bloggs"

# The date the test was created using pysys make. If you copy an existing test you'd have to manually set this.
__pysys_created__ = "2021-07-25"

# Use this to list traceability ids for the requirements validated by this test, such as defect or user story ids.
__pysys_traceability_ids__ = "Bug-1234, UserStory-456, UserRequirement_1a, UserRequirement_2c, Performance" 

# Comment/uncomment this to mark this test as skipped, which will stop it from executing.
__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed" 

# Specify the groups that this test will be tagged with, allowing them to be selected for inclusion/exclusion in test 
# runs. Groups are usually named in camelCase. These groups are separated by commas, followed by a semi-colon and 
# inherit=true/false which specifies whether groups from parent pysysdirconfigs are inherited by this test. 
#
# The disableCoverage group is a special group used by code coverage writers to ensure coverage tools are disabled for 
# tests that are performance-critical. By default groups inherit, but you can override that with "; inherit=false". 
__pysys_groups__           = "performance, disableCoverage; inherit=true"

# Specify the list of modes this test can be run in. 
#
# Like test ids, mode names are usually TitleCase, with multiple dimensions delimited by an ``_`` underscore, 
# e.g. ``CompressionGZip_AuthNone``.
# 
# Test modes are configured with a Python lambda that returns a list of modes, using a single parameter which is 
# an instance of ``pysys.config.descriptor.TestModesConfigHelper`` providing access to the inherited modes (and other 
# useful functions/fields). Each mode in the returned list is defined by a dictionary containing parameters to be set 
# on the test object and/or a ``mode`` name. If the mode name is not explicitly provided, a default mode name is 
# generated by concatenating the parameter values with ``_`` (with a ``paramName=`` prefix for any numeric/boolean 
# values). Note that (for now, for technical parsing reasons) the lambda must be enclosed in a Python string.
#
# In your Python lambda you can return a simple list of modes, or combine your own modes with inherited modes 
# defined by parent pysysdirconfigs. You can also use the power of Python list comprehensions to exclude certain modes, 
# perhaps based on dynamic information such as the operating system. Project properties can be accessed 
# using ``helper.project.PROPERTY_NAME``. Avoid expensive operations such as reading the file system from your lambda 
# if possible. 
# 
# An alternative to providing a list of dicts for each mode is to provide a dict whose keys are the mode names and 
# values are dicts containing the parameters. 
#
# By default the first mode in each dimension is designated a *primary* mode (one that executes by default 
# when no ``--modes`` argument is specified), but this can be overridden by setting ``'isPrimary': True/False`` 
# in the dict for any mode. When mode dimensions are combined, a mode is primary is all the modes it is derived from 
# were designated primary. When using modes for different execution environments/browsers etc you probably want only 
# the first (typically fastest/simplest/most informative) mode to be primary, on the other hand if using modes to 
# execute the same Python logic against various input files/args you should usually set all of the modes to be primary. 
#
# It's often useful to combine multiple mode 'dimensions', for example all the combinations of a list of web browsers 
# with a list of databases, or compression methods and authentication types. Rather than writing out every combination 
# manually, you can use the function ``helper.combineModeDimensions`` to automatically generate all combinations. 
#
# Modes can be used to define multiple tests that share the same test class logic, for example testing your 
# application's output when given various different input test vectors. For this use case, if you already (or 
# plan to) define multiple execution modes inherited in a parent directory, you usually want to 
# use ``helper.combineModeDimensions(helper.inheritedModes, helper.makeAllPrimary({...}))`` in your test so that each 
# of the test scenarios you define in that second argument are executed in each of the inherited modes (if any). 
#
# A test can use self.mode to find out which mode it is executing and/or self.mode.params to access any parameters.
#
__pysys_modes__            = lambda helper: [
			mode for mode in 
				helper.combineModeDimensions( # Takes any number of mode lists as arguments and returns a single combined mode list
					helper.inheritedModes,
					{
							'CompressionNone': {'compressionType':None, 'isPrimary':True}, 
							'CompressionGZip': {'compressionType':'gzip'},
					}, 
					[
						{'auth':None}, # Mode name is optional
						{'auth':'OS'}, # In practice auth=OS modes will always be excluded since MyFunkyOS is a fictional OS
					], 
					
					# By default only the first mode in each list is "primary", so the test will only run in that one mode by 
					# default during local development (unless you supply a ``--modes`` or ``--ci`` argument). This is optimal when 
					# using modes to validate the same behaviour/conditions in different execution environments e.g. 
					# browsers/databases etc. However when using modes to validate different *behaviours/conditions* (e.g. testing 
					# out different command line options) using a single PySysTest class, then you should have all your modes as 
					# "primary" as you want all of them to execute by default in a quick local test run. 
					helper.makeAllPrimary(
						{
							'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
							'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
							'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
						}), 
					)
				
			# This is Python list comprehension syntax for filtering the items in the list
			if (mode['auth'] != 'OS' or helper.import_module('sys').platform == 'MyFunkyOS')
		]

# Specify as a floating point number an indicator of when to run the tests under this directory, relative to other 
# tests/directories with a higher or lower hint. 
# The default priority is 0.0 so set the hint to a higher value to execute tests later, or a negative value to execute 
# tests earlier. 
# Comment this out to inherit from parent pysysdirconfig.xml files. 
__pysys_execution_order_hint__ = +100.0
	
# By default the test class uses this pysystest.py module, but it is possible to use a different path for the test 
# (even an absolute path). If you want to use a single Python class for lots of tests, set the module 
# to the special string "PYTHONPATH" and make sure it's available on the project's <pythonpath>. 
__pysys_python_class__     = "PySysTest"
__pysys_python_module__    = "${testRootDir}/pysys-extensions/MySharedTestClass.py" # or "PYTHONPATH"

# You can customize the Input/Output/Reference directory names if you wish (or even provide an absolute 
# paths if needed). These can also be specified using the older names <output/input/reference> with a path= attribute. 
# In practice it is usually best to set this configuration in pysysproject.xml or pysysdirconfig.xml rather than 
# in individual tests. 
__pysys_input_dir__        = "${testRootDir}/pysys-extensions/my_shared_input_files"
__pysys_reference_dir__    = "MyReference"
__pysys_output_dir__       = "MyOutput"

# The ability to add user-defined data to the test descriptor is mostly useful when using a shared Python class for 
# lots of tests, or for passing data from a pysystest.* file in a language other than Python into the descriptor 
# for reading by Python code. 
__pysys_user_data__        = {
	
		'myTestDescriptorData': 'foobar', 

		# For long values such as paths if the value is to be converted to a list, newline and/or comma can be used as 
		# delimiters, however it is up to the Python code that's processing the user data to handle. 
		# Similarly, you can use project property syntax (e.g. ${propName} or ${eval: xxx}) if the code that reads 
		# the user data expands them (but this does not happen automatically). 
		'myTestDescriptorPath': '''
			foo/foo-${os_myThirdPartyLibraryVersion}
			foo/bar, foo/baz

			foo/bosh
		'''
	}

# It is also possible to provide the descriptor values using XML embedded in this file as follows. Note that parsing 
# XML is relatively slow, so add this value only if you have a good reason. 
__pysys_xml_descriptor__ = r"""
	<?xml version="1.0" encoding="utf-8"?>
	<pysystest>
	
	</pysystest>
"""

# All __pysys_XXX__ descriptor values must be specified before the import statements and class definition. 

import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pass

	def validate(self):
		pass
	