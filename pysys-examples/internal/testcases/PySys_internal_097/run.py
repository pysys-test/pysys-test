import pysys
from pysys.constants import *
from pysys.basetest import BaseTest
from pysys.utils.perfreporter import CSVPerformanceFile
import os, sys, math, shutil

class PySysTest(BaseTest):

	def execute(self):
		l = {}
		exec(open(os.path.normpath(self.input+'/../../../utilities/resources/runpysys.py')).read(), {}, l) # define runPySys
		runPySys = l['runPySys']
		
		shutil.copytree(self.input, self.output+'/test')
		
		for subtest in ['none', 'lang', 'legacy', 'tempdir']:
			runPySys(self, 'pysys', ['run', '-o', self.output+'/pysys-'+subtest], workingDir='test', 
				environs={'SOME_OVERRIDE':'some value'},
				projectfile='pysysproject-%s.xml'%subtest)
			self.logFileContents('pysys-%s.out'%subtest, maxLines=0)
			
	def validate(self):
		# inherited environment not passed on, unles in legacy mode on Windows
		self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='SOME_OVERRIDE=', contains=False)
		if IS_WINDOWS:
			self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='SOME_OVERRIDE=some value')
			self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='PATHEXT=')
		else:
			# empty environment
			self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='.', contains=False)

		# python setting
		if IS_WINDOWS:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='LD_LIBRARY', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='PATH=.*python')
		else:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='PATH=.*python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='LD_LIBRARY_PATH=.*python')
		self.assertGrep('pysys-none/PySys_NestedTestcase/python.out', expr='Python executed successfully')

		self.assertTrue(os.path.exists(self.output+'/pysys-tempdir/PySys_NestedTestcase/mytemp'), assertMessage='tempdir was created')
		self.assertGrep('pysys-tempdir/PySys_NestedTestcase/python.out', expr='TempDir=.*PySys_NestedTestcase.mytemp')

		if IS_WINDOWS:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='LANG', contains=False)
		else:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='LANG=my-lang')
