__pysys_title__   = r""" My testcase @TEST_ID@""" 
#                        ================================================================================

__pysys_purpose__ = r""" The purpose of this test is to check that 
	argument parsing addresses these criteria:
		- Correctness
		- Clear error messages
	""" 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2021-12-27"

__pysys_groups__           = "group1, group2; inherit=true"
__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

__pysys_traceability_ids__ = "Bug-1234, UserStory-456, UserRequirement_1a, UserRequirement_2c, Performance" 

__pysys_modes__            = """lambda helper: [
			mode for mode in 
				helper.createModeCombinations( # Takes any number of mode lists as arguments and returns a single combined mode list
					helper.inheritedModes,
					{
							'CompressionNone': {'compressionType':None, 'isPrimary':True}, 
							'CompressionGZip': {'compressionType':'gzip'},
					}, 
					[
						{'auth':None}, # Mode name is optional
						{'auth':'OS'}, # In practice auth=OS modes will always be excluded since MyFunkyOS is a fictional OS
					], 
					
					helper.makeAllPrimary(
						{
							'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
							'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
							'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
						}), 
					)
				
			if (mode['auth'] != 'OS')
		]"""

__pysys_execution_order_hint__ = +100.0
	
__pysys_python_class__     = "PySysTest"
__pysys_python_module__    = "${testRootDir}/pysys-extensions/MySharedTestClass.py" # or "PYTHONPATH"

__pysys_input_dir__        = "${testRootDir}/pysys-extensions/my_shared_input_files"
__pysys_reference_dir__    = "MyReference"
__pysys_output_dir__       = "MyOutput"

__pysys_user_data__        = r"""
	{
	
		'myTestDescriptorData': 'foobar', 

		'myTestDescriptorPath': '''
			foo/foo-${startDate}
			foo/bar, foo/baz

			foo/bosh
		'''
	}
	"""

import os, sys, math, shutil

import pysys
from pysys.constants import *
#from pysys.basetest import BaseTest

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.copy(self.input, self.output+'/test')
		if self.project in [1, 2, 3, 4, 5, 6, 7, 8]:
			self.skipTest('Foo bar')

	def validate(self):
		self.addOutcome(PASSED, '')
		self.assertGrep('foo.out', 'abc.*')
		self.assertGrep('foo.out', 'abc1.*')
		self.assertGrep('foo.out', 'abc2.*')
		self.assertGrep('foo.out', 'abc3.*')
		self.assertGrep('foo.out', 'abc4.*')
		self.assertGrep('foo.out', 'abc5.*')
		self.assertGrep('foo.out', 'abc6.*')
		self.assertGrep('foo.out', 'abc7.*')
		self.assertGrep('foo.out', 'abc8.*')
		self.assertGrep('foo.out', 'abc9.*')
		self.assertGrep('foo.out', 'abc10.*')
		self.assertGrep('foo.out', 'abc11.*')
		for i in range(20):
			self.assertGrep('foo.out', 'abc12xxxx.*')
