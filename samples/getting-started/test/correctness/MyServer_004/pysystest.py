__pysys_title__   = r""" MyServer startup - arg parsing edge cases (+ demo of using modes to cover different test scenarios) """
#                        ===============================================================================

__pysys_purpose__ = r""" To demonstrate error messages for unsuccessful startup of MyServer. 
	
	This also shows how modes can be used to cover different test scenarios from the same PySysTest class. 
	"""

__pysys_created__ = "1999-12-31"

__pysys_groups__  = "myServerStartup"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

# This configures a named "mode" where the entire test runs with each self.mode.params dict listed below:
__pysys_parameterized_test_modes__  = {
	'Usage': {
		'cmd': ['--help'], 
		'expectedExitStatus':'==0', 
		'expectedMessage':None}, 
	'BadPort': {
		'cmd': ['--port', '-1'],  
		'expectedExitStatus':'!=0', 
		'expectedMessage':'Server failed: Invalid port number specified: -1'}, 
	'SetPortTwice': {
		'cmd': ['--port', '123', '--config', '@TEST_DIR@/myserverconfig.json'], 
		'expectedExitStatus':'!=0', 
		'expectedMessage':'Server failed: Cannot specify port twice'}, 
	}

import pysys.basetest, pysys.mappers
from pysys.constants import *

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		server = self.startProcess(
			command=self.project.appHome+'/my_server.%s'%('bat' if IS_WINDOWS else 'sh'), 
			arguments=[arg.replace('@TEST_DIR@', self.descriptor.testDir) for arg in self.mode.params['cmd']], 
			environs=self.createEnvirons(addToExePath=os.path.dirname(PYTHON_EXE), command=PYTHON_EXE),
			stdouterr='my_server', 
			displayName=f'my_server<{self.mode.params["cmd"]}>', 
			
			# This is an example of using mode parameters to help with validating correct behaviour:
			expectedExitStatus=self.mode.params['expectedExitStatus']
			
			)
		
		self.logFileContents(server.stderr)
		self.logFileContents(server.stdout)
		
	def validate(self):	
		self.assertGrep('my_server.err', r'.*', contains=False) # should be nothing on stderr

		if self.mode.params['expectedMessage']:
			self.assertThatGrep('my_server.out', r' ERROR (.*)', 'value == expected', expected=self.mode.params['expectedMessage'])
		else:
			self.assertDiff('my_server.out', self.mode+'.my_server.out')
		