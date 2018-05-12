from pysys.baserunner import BaseRunner
from pysys.constants import *
import logging, os

class MyCustomRunner(BaseRunner):
	currentcycle = 0
	
	def cycleComplete(self):
		"""Cycle complete method which may optionally be overridden to perform custom operations between the repeated execution of a set of testcases.
		
		"""
		self.currentcycle += 1
		self.log.info('Called BaseRunner.cycleComplete for cycle %d'%self.currentcycle)
