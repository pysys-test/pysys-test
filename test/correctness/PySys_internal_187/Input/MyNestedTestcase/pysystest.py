__pysys_title__   = r""" Python Thread logging and error handling """ 
#                        ================================================================================
__pysys_purpose__ = r""" Check people not using self.startBackgroundThread can still get sensible logging. """ 
	
__pysys_authors__ = "bsp"
__pysys_created__ = "2022-11-21"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 
#__pysys_groups__           = "myGroup, disableCoverage, performance"
#__pysys_modes__            = lambda helper: helper.inheritedModes + [ {'mode':'MyMode', 'myModeParam':123}, ]
#__pysys_parameterized_test_modes__ = {'MyParameterizedSubtestModeA':{'myModeParam':123}, 'MyParameterizedSubtestModeB':{'myModeParam':456}, }

import os, sys, math, shutil, time
import concurrent.futures

import pysys.basetest, pysys.mappers
from pysys.constants import *

import logging
import threading

class PySysTest(pysys.basetest.BaseTest):

	def execute(self):
		def waiter():
			self.log.info('Background thread has started waiting')
			time.sleep(1.5)
			self.log.info('Background thread has completed waiting')

		def raiser(): 
			logging.getLogger('pysys.foo').info('Log message from submitted thread job')
			raise Exception('My exception from thread job')
	
		tp = self.createThreadPoolExecutor()
		self.assertThat('expected == actual', actual__eval="list(tp.map(lambda x: x+1, [1,2,3]))", expected=[2,3,4])
		tp.submit(waiter)

		concurrent.futures.wait([tp.submit(raiser)])

		self.log.info('Creating second thread pool:')
		with self.createThreadPoolExecutor(): # not recommended, but check it doesn't error during shutdown if someone does this
			pass

	def validate(self):
		pass
