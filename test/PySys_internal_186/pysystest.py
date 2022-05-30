__pysys_title__   = r""" Process - Windows command line quoting """ 
#                        ================================================================================
__pysys_purpose__ = r"""
Check that some weird edge cases when quoting Windows command lines are handled,
and that quoted command lines are parsed the way we expect them to be.
""" 
	
__pysys_authors__ = "rsm31"
__pysys_created__ = "2022-05-30"
#__pysys_skipped_reason__   = "Skipped until Bug-1234 is fixed"

#__pysys_traceability_ids__ = "Bug-1234, UserStory-456" 

import pysys
from pysys.constants import *
from pysys.process.helper import ProcessImpl

import os, sys, math, shutil, glob
import win32api

class PySysTest(pysys.basetest.BaseTest):

	def setup(self):
		self.pimpl = ProcessImpl("", [], self.createEnvirons(), "", FOREGROUND, 0)

	def __buildCmdLine(self, command, args):
		cmdline = self.pimpl._ProcessImpl__quotePath(command)
		for arg in args: cmdline = '%s %s' % (cmdline, self.pimpl._ProcessImpl__quotePath(arg))
		return cmdline

	def __testCmdLine(self, command, args):
		cmdline = self.__buildCmdLine(command, args)
		oldargv = [command] + args
		newargv = win32api.CommandLineToArgv(cmdline)
		self.log.info("Original: %s" % oldargv)
		self.log.info("Quoted:   %s" % cmdline)
		self.log.info("Parsed:   %s" % newargv)
		if newargv != oldargv:
			self.addOutcome(FAILED, "Parsed command line does not match original")
			self.log.warn("  Original: %s" % oldargv)
			self.log.warn("  Quoted:   %s" % cmdline)
			self.log.warn("  Parsed:   %s" % newargv)

	def execute(self):
		if not IS_WINDOWS:
			self.skipTest('This test is only useful on Windows')

		self.__testCmdLine('C:\\dir\\program.exe', ["C:\\"])
		self.__testCmdLine('C:\\dir\\program.exe', ["arg1", "arg2", "arg3"])
		
	def validate(self):
		pass