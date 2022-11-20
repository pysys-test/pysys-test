__pysys_title__   = r""" Process Module - benchmark Windows command line generation algorithms """
#                        ================================================================================
__pysys_purpose__ = r"""
Compare performance of old (simple but incomplete) and new (correct but complex)
algorithms for generating Windows command lines from a command + argv list.
""" 
	
__pysys_authors__ = "rsm31"
__pysys_created__ = "2022-06-11"
__pysys_groups__           = "process, performance, disableCoverage; inherit=true"
__pysys_traceability_ids__ = "https://github.com/pysys-test/pysys-test/issues/65" 

import pysys
from pysys.constants import *
from pysys.perf.api import PerformanceUnit
from pysys.process.helper import ProcessImpl

import time

class PySysTest(pysys.basetest.BaseTest):

	testDurationSecs = 10.0
	useLegacyAlgorithm = False	# Set this to use a replica of the old algorithm

	def setup(self):
		# We need a ProcessImpl so we can call its private methods
		self.pimpl = ProcessImpl("", [], self.createEnvirons(), "", FOREGROUND, 0)

	def oldQuoteCommandLine(self, command, args):
		""" Old Windows command line quoting implementation

		This algorithm doesn't work correctly for every weird edge case.
		It is reproduced here so we can compare its performance to the new one.
		"""
		cmdline = '\"%s\"'%command.replace('"', '""')
		for arg in args:
			cmdline = '%s %s' % (cmdline, '\"%s\"'%arg.replace('"', '""'))
		return None, cmdline
	
	def testCommandLine(self, command, args, description):
		""" Measure command line generation rate over testDurationSecs seconds

		Adds a performance result with the supplied description in its name.
		"""
		starttime = time.time()
		endtime  = starttime+float(self.testDurationSecs)
		iterations = 0
		while time.time() < endtime:
			iterations += 1
			newcmd, cmdline = self.testFn(command, args)
		rate = iterations / (time.time() - starttime)
		self.reportPerformanceResult(rate, 'Command line generation rate (%s)' % description, '/s')

	def execute(self):
		if not IS_WINDOWS:
			self.skipTest('This test is only useful on Windows')

		if self.useLegacyAlgorithm:
			self.testFn = self.oldQuoteCommandLine
		else:
			self.testFn = self.pimpl._ProcessImpl__buildCommandLine

		command = 'program.exe'
		args = []
		self.testCommandLine(command, args, '1: command / no args')

		command = 'C:\\path\\program.exe'
		args = []
		self.testCommandLine(command, args, '2: command with path / no args')

		command = 'C:\\path with spaces\\program.exe'
		args = []
		self.testCommandLine(command, args, '3: command with spaces / no args')

		command = 'program.exe'
		args = 10 * ['a_simple_argument']
		self.testCommandLine(command, args, '4: simple args')

		command = 'program.exe'
		args = 10 * ['C:\\argument\\path']
		self.testCommandLine(command, args, '5: args with path')

		command = 'program.exe'
		args = 10 * ['a simple argument']
		self.testCommandLine(command, args, '6: args with spaces')

		command = 'program.exe'
		args = 10 * ['a"simple"argument']
		self.testCommandLine(command, args, '7: args with quotes')

		command = 'program.exe'
		args = 10 * ['a \\\\"very\\\\ ""complex"" argument\\']
		self.testCommandLine(command, args, '8: complex args')

	def validate(self):
		self.addOutcome(PASSED)
