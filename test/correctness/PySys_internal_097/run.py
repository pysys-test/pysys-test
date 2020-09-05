import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

if PROJECT.testRootDir+'/internal/utilities/extensions' not in sys.path:
	sys.path.append(PROJECT.testRootDir+'/internal/utilities/extensions') # only do this in internal testcases; normally sys.path should not be changed from within a PySys test
from pysysinternalhelpers import *

class PySysTest(BaseTest):

	def execute(self):
		self.log.info('Using python from     %s', sys.executable)
		self.log.info('With python libs from %s', os.__file__)
	
		self.copy(self.input, self.output+'/test')
		
		for subtest in ['none', 'lang', 'legacy', 'tempdir']:
			runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-'+subtest], workingDir='test', 
				environs={'SOME_OVERRIDE':'some value'},
				projectfile='pysysproject-%s.xml'%subtest)
			self.logFileContents('pysys-%s.out'%subtest, maxLines=0)
			
	def validate(self):
		env = self.createEnvirons(addToLibPath='my-lib-path', addToExePath=['my-exe-path1', 'my-exe-path2'])
		self.log.info('Created environs: %s', env)
		self.assertThat('"my-exe-path1'+os.pathsep+'my-exe-path2" in %s', repr(env['PATH']))
		self.assertThat('"my-lib-path" in %s', repr(env[LIBRARY_PATH_ENV_VAR]))
	
		# inherited environment not passed on, unles in legacy mode on Windows
		self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='SOME_OVERRIDE=', contains=False)

		if IS_WINDOWS:
			self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='^SOME_OVERRIDE=some value')
			self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='^PATHEXT=')
		else:
			# depending on where python is installed, empty environment might mean we can't even start python
			# or it might start and print an empty environment
			if os.path.exists(self.output+'/pysys-legacy/PySys_NestedTestcase/python.err'):
				self.assertGrep('pysys-legacy/PySys_NestedTestcase/python.err', expr='.+')
			else:
				self.logFileContents('pysys-legacy/PySys_NestedTestcase/python.out')
				self.assertGrep('pysys-legacy/PySys_NestedTestcase/python.out', expr='Python environment: [.]')

		# python setting - affects PYTHONHOME, LD_LIB and executable PATH
		self.logFileContents('pysys-none/PySys_NestedTestcase/env-python.txt')
		if IS_WINDOWS:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='LD_LIBRARY', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='^PATH=.+')
		else:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='%s=.+'%LIBRARY_PATH_ENV_VAR)
			self.logFileContents('pysys-none/PySys_NestedTestcase/env-python.txt')
		self.assertGrep('pysys-none/PySys_NestedTestcase/python.out', expr='Python executed successfully')

		self.assertPathExists('pysys-tempdir/PySys_NestedTestcase/mytemp')
		self.assertGrep('pysys-tempdir/PySys_NestedTestcase/python.out', expr='TempDir=.*[Nn]ested[Tt]estcase.mytemp')

		if IS_WINDOWS:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='^LANG', contains=False)
		else:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='^LANG=my-lang')
		self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='^JAVA_TOOL_OPTIONS=-Xmx512M')
