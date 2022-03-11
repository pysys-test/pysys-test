__pysys_title__   = r""" fileutils - deleteDir when readonly attribute or permissions are set""" 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-03-10"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import pysys
from pysys.constants import *

import os, sys, math, shutil, glob
import stat

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		self.mkdir('locked-directory')
		self.write_text('locked-directory/locked-file.txt', 'Hello')
		if IS_WINDOWS:
			import win32api, win32con
			win32api.SetFileAttributes(self.output+'/locked-directory/locked-file.txt', win32con.FILE_ATTRIBUTE_READONLY)
			win32api.SetFileAttributes(self.output+'/locked-directory', win32con.FILE_ATTRIBUTE_READONLY)
		else:
			for path in [self.output+'/locked-directory/locked-file.txt', self.output+'/locked-directory']:
				os.chmod(path, 0) # deny all permissions

		self.deleteDir('locked-directory')
		self.assertPathExists('locked-directory', exists=False)
		
	def validate(self):
		pass
