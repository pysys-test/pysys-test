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
		# We need a ProcessImpl so we can call its private methods
		self.pimpl = ProcessImpl("", [], self.createEnvirons(), "", FOREGROUND, 0)

	def __buildCmdLine(self, command, args):
		# Build a command line the same way startBackgroundProcess() does
		cmdline = self.pimpl._ProcessImpl__quotePath(command)
		for arg in args: cmdline = '%s %s' % (cmdline, self.pimpl._ProcessImpl__quotePath(arg))
		return cmdline

	def testCmdLine(self, command, args, expected=None):
		""" Test parsing of a command line built from a command + argument list
		
		Success means:
		1. The quoted/escaped command line matches the expected one (if provided)
		2. CommandLineToArgv() on the command line gets back the original arguments
		"""
		cmdline = self.__buildCmdLine(command, args)
		oldargv = [command] + args
		newargv = win32api.CommandLineToArgv(cmdline)
		self.log.info("Original: %s" % oldargv)
		self.log.info("Quoted:   %s" % cmdline)
		self.log.info("Parsed:   %s" % newargv)
		if expected and expected != cmdline:
			self.addOutcome(FAILED, "Quoted command line does not match expected")
			self.log.warn("  Original: %s" % oldargv)
			self.log.warn("  Expected: %s" % expected)
			self.log.warn("  Quoted:   %s" % cmdline)
		if newargv != oldargv:
			self.addOutcome(FAILED, "Parsed command line does not match original")
			self.log.warn("  Original: %s" % oldargv)
			self.log.warn("  Parsed:   %s" % newargv)

	def execute(self):
		if not IS_WINDOWS:
			self.skipTest('This test is only useful on Windows')

		# TODO - Test cases to be covered:
		# 1. Special characters in argv[1..]
		#    - Inline whitespace (space & tab)
		#    - Inline double quotes
		#    - Inline backslashes (and sequences)
		#    - Trailing whitespace
		#    - Trailing double quotes
		#    - Trailing backslashes
		# 2. Special handling for argv[0]
		# 3. Weird rules for cmd.exe /c and /k options

		self.testCmdLine('C:\\dir\\program.exe', ["C:\\"])
		self.testCmdLine('C:\\dir\\program.exe', ["arg1", "arg2", "arg3"])
		
	def validate(self):
		pass