__pysys_title__   = r""" Cgroups support - some cgroups configuration is read from OS if present """ 
#                        ================================================================================
__pysys_purpose__ = r""" """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2023-02-07"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import os, sys, math, shutil, glob

import pysys.basetest, pysys.mappers
from pysys.constants import *

from pysysinternalhelpers import PySysTestHelper

class PySysTest(PySysTestHelper, pysys.basetest.BaseTest):

	def execute(self):
		if IS_WINDOWS or not os.path.exists('/sys/fs/cgroup'): self.skipTest('/sys/fs/cgroup is not present/supported on this OS')

		self.pysys.pysys('pysys-run', ['run', '-o', self.output+'/myoutdir', '-vpysys.cgroups=DEBUG', '-vCRIT'], workingDir=self.input)
		self.logFileContents('pysys-run.out')
		
	def validate(self):
		self.assertGrep('pysys-run.out', 'Failed to read cgroups', contains=False)
		v = 2 if os.path.exists('/sys/fs/cgroup/cgroup.controllers') else 1
		self.log.info('Testing for cgroups version: %s'%v)
		if v == 1:
			self.assertGrep('pysys-run.out', 'DEBUG +Reading cgroup configuration for cpu controller from "/sys/fs/cgroup/.*cpu')
			self.assertThatGrep('pysys-run.out', 'DEBUG +Read cgroups configuration: v1 cpu.cfs_quota_us/cfs_period_us=([^ ]+)', "re.match(validationRegex, value)", 
		       validationRegex=r'(-1|[0-9]+)/[0-9]+')
		else:
			self.assertGrep('pysys-run.out', 'DEBUG +Reading cgroup configuration for <cgroup v2> controller from "/sys/fs/cgroup.*')
			self.assertThatGrep('pysys-run.out', 'DEBUG +Read cgroups configuration: .*v2 (cpu.max=.+);', "re.match(validationRegex, value)", 
		       validationRegex=r"cpu.max=([?]|max/[0-9]+|[0-9]+/[0-9]+)")
		