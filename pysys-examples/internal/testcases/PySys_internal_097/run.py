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
			# depending on where python is installed, empty environment might mean we can't even start python
			# or it might start and print an empty environment
			if os.path.exists(self.output+'/pysys-legacy/PySys_NestedTestcase/env.txt'):
				self.assertGrep('pysys-legacy/PySys_NestedTestcase/env.txt', expr='.+', contains=False)
			else:
				self.assertGrep('pysys-legacy/PySys_NestedTestcase/python.err', expr='.+')

		# python setting - affects PYTHONHOME, LD_LIB and executable PATH
		if IS_WINDOWS:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='LD_LIBRARY', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='PATH=.*python')
		else:
			self.assertGrep('pysys-none/PySys_NestedTestcase/env.txt', expr='python', contains=False)
			self.assertGrep('pysys-none/PySys_NestedTestcase/env-python.txt', expr='LD_LIBRARY_PATH=.+')
			self.logFileContents('pysys-none/PySys_NestedTestcase/env-python.txt')
		self.assertGrep('pysys-none/PySys_NestedTestcase/python.out', expr='Python executed successfully')

		self.assertTrue(os.path.exists(self.output+'/pysys-tempdir/PySys_NestedTestcase/mytemp'), assertMessage='tempdir was created')
		self.assertGrep('pysys-tempdir/PySys_NestedTestcase/python.out', expr='TempDir=.*[Nn]ested[Tt]estcase.mytemp')

		if IS_WINDOWS:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='LANG', contains=False)
		else:
			self.assertGrep('pysys-lang/PySys_NestedTestcase/env.txt', expr='LANG=my-lang')
