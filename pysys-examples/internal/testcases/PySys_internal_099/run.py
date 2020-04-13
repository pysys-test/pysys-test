# -*- coding: latin-1 -*-
import glob
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pysysroot = os.path.dirname(os.path.dirname(pysys.__file__))
		
		distinfo = glob.glob(pysysroot+'/PySys*dist-info*') # created when installing from whl
		
		rootdocs = ['README.rst', 'LICENSE.txt', 'CHANGELOG.rst']
		
		self.log.info('PySys root directory is %s', pysysroot)
		self.log.info('')
		#self.log.info('   Files are: %s', sorted(os.listdir(pysysroot)))
		self.log.info('')
		
		self.log.info('   Binary distinfo exists=%s', distinfo)
		isSourceDist = os.path.exists(pysysroot+'/'+rootdocs[0])
		self.log.info('   Source dist     exists=%s', isSourceDist)
		self.assertThat('(%s or %s)', bool(distinfo), isSourceDist)
		self.log.info('')
		if distinfo:
			#self.log.info('Binary dist info contains: %s', sorted(os.listdir(distinfo[0])))
			for d in rootdocs:
				self.assertThat('os.path.exists(%s)', repr(distinfo[0]+'/'+d))
		self.log.info('')
		if isSourceDist:
			for d in rootdocs:
				self.assertThat('os.path.exists(%s)', repr(pysysroot+'/'+d))

		# since our automated testing covers the fibonacci pysysdirconfig, use an 
		# assert to check that the template included with the distribution itself 
		# (which currently doen't have independent testing) is the same
		self.assertDiff(self.project.testRootDir+'/fibonacci/testcases/pysysdirconfig.xml', pysysroot+'/pysys/xml/templates/dirconfig/default.xml')
		
	def validate(self):
		pass