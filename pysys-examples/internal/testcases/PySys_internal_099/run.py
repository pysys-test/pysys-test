# -*- coding: latin-1 -*-
import glob
import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):
	def execute(self):
		pysysroot = os.path.dirname(os.path.dirname(pysys.__file__))
		
		distinfo = glob.glob(pysysroot+'/PySys*dist-info*') # created when installing from whl
		
		rootdocs = ['README.rst', 'LICENSE.txt', 'CHANGELOG.rst', 'docs/BaseTest.rst', 'docs/UserGuide.rst']
		
		self.log.info('PySys root directory is %s', pysysroot)
		self.log.info('')
		#self.log.info('   Files are: %s', sorted(os.listdir(pysysroot)))
		self.log.info('')
		
		self.log.info('   Binary distinfo exists=%s', distinfo)
		isSourceDist = os.path.exists(pysysroot+'/'+rootdocs[0])
		self.log.info('   Source dist     exists=%s', isSourceDist)
		self.assertEval('bool({binary_whl_distinfo}) or {isSourceDist}', binary_whl_distinfo=distinfo, isSourceDist=isSourceDist)
		self.log.info('')
		if distinfo:
			#self.log.info('Binary dist info contains: %s', sorted(os.listdir(distinfo[0])))
			for d in rootdocs:
				self.assertPathExists(distinfo[0]+'/'+os.path.basename(d))
		self.log.info('')
		if isSourceDist:
			for d in rootdocs:
				self.assertPathExists(pysysroot+'/'+d)

	def validate(self):
		pass
	