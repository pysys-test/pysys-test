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

	def testCmdLine(self, command, args, expected=None):
		""" Test parsing of a command line built from a command + argument list
		
		Success means:
		1. The quoted/escaped command line matches the expected one (if provided)
		2. CommandLineToArgv() on the command line gets back the original arguments
		"""
		newcmd, cmdline = self.pimpl._ProcessImpl__buildCommandLine(command, args)
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

		# No special characters in arguments
		self.testCmdLine('program.exe', ['arg1', 'arg2', 'arg3'], 'program.exe arg1 arg2 arg3')

		# Whitespace (space and tab) in arguments
		self.testCmdLine('program.exe', ['arg 1', 'arg2', 'a r g 3'], 'program.exe arg" "1 arg2 a" "r" "g" "3')
		self.testCmdLine('program.exe', ['arg\t1', 'arg2', 'a\tr\tg\t3'], 'program.exe arg"\t"1 arg2 a"\t"r"\t"g"\t"3')
		self.testCmdLine('program.exe', ['a\tr g\t1', 'arg2', 'a\tr g\t3'], 'program.exe a"\t"r" "g"\t"1 arg2 a"\t"r" "g"\t"3')

		# Double quotes in arguments
		self.testCmdLine('program.exe', ['arg"1', 'arg2', 'a"r"g"3'], 'program.exe arg\\"1 arg2 a\\"r\\"g\\"3')
		self.testCmdLine('program.exe', ['arg""1', 'arg2', 'a"""r""""g"""""3'], 'program.exe arg\\"\\"1 arg2 a\\"\\"\\"r\\"\\"\\"\\"g\\"\\"\\"\\"\\"3')

		# Backslashes in arguments
		self.testCmdLine('program.exe', ['a\\r\\g\\1', 'arg2', '\\arg3\\'], 'program.exe a\\r\\g\\1 arg2 \\arg3\\')
		self.testCmdLine('program.exe', ['a\\\\r\\\\\\g\\\\\\\\1', 'arg2', '\\\\arg3\\\\'], 'program.exe a\\\\r\\\\\\g\\\\\\\\1 arg2 \\\\arg3\\\\')

		# Mixed special characters in arguments
		self.testCmdLine('program.exe', ['a "r" g\\1', 'arg2', 'arg3'], 'program.exe a" "\\"r\\"" "g\\1 arg2 arg3')
		
	def validate(self):
		pass