#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA



"""
Writers that record test outcomes on the console (stdout) when running PySys. 

If no progress writers are explicitly configured in the PySys project XML file, an instance of
`ConsoleProgressResultsWriter` is used. If no summary writer is explicitly configured in the PySys project
XML file, an instance of `ConsoleSummaryResultsWriter` is used.

"""

__all__ = [
	"ConsoleSummaryResultsWriter", "ConsoleProgressResultsWriter", "ConsoleFailureAnnotationsWriter"]

import time, stat, logging, sys, io
import zipfile
import locale
import shutil
import shlex

from pysys.constants import *
from pysys.writer.api import *
from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes, stdoutPrint
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2, openfile
from pysys.exceptions import UserError

log = logging.getLogger('pysys.writer')

class ConsoleSummaryResultsWriter(BaseSummaryResultsWriter, TestOutcomeSummaryGenerator):
	"""Default summary writer that is used to list a summary of the test results at the end of execution.

	Support the same configuration options as `pysys.writer.api.TestOutcomeSummaryGenerator`.
	"""
	# change some of the TestOutcomeSummaryGenerator defaults for the console
	showOutcomeReason = True
	showOutputDir = True
	showDuration = True
	showTestIdList = True
	showRunDetails = True
	
	def cleanup(self, **kwargs):
		log = logging.getLogger('pysys.resultssummary')
		log.critical("")
		self.logSummary(log.critical)

class ConsoleProgressResultsWriter(BaseProgressResultsWriter):
	"""Default progress writer that logs a summary of progress so far to the console, after each test completes.

	"""
	def __init__(self, **kwargs):
		self.recentFailures = 5  # configurable

	def setup(self, cycles=-1, numTests=-1, threads=-1, **kwargs):
		super(ConsoleProgressResultsWriter, self).setup(cycles=cycles, numTests=numTests, threads=threads, **kwargs)
		self.cycles = cycles
		self.numTests = numTests
		self.startTime = time.time()

		self.outcomes = {}
		for o in OUTCOMES: self.outcomes[o] = 0
		self._recentFailureReasons = []
		self.threads = threads
		self.inprogress = set() # this is thread-safe for add/remove

	def processTestStarting(self, testObj, cycle=-1, **kwargs):
		self.inprogress.add(self.testToDisplay(testObj, cycle))

	def testToDisplay(self, testObj, cycle):
		id = testObj.descriptor.id
		if self.cycles > 1: id += ' [CYCLE %02d]'%(cycle+1)
		return id

	def processResult(self, testObj, cycle=-1, **kwargs):
		if self.numTests == 1: return
		log = logging.getLogger('pysys.resultsprogress')
		
		id = self.testToDisplay(testObj, cycle)
		self.inprogress.remove(id)
		
		outcome = testObj.getOutcome()
		self.outcomes[outcome] += 1
		
		executed = sum(self.outcomes.values())
		
		if outcome.isFailure():
			m = '%s: %s'%(outcome, id)
			if testObj.getOutcomeReason(): m += ': '+testObj.getOutcomeReason()
			self._recentFailureReasons.append(m)
			self._recentFailureReasons = self._recentFailureReasons[-1*self.recentFailures:] # keep last N
		
		# nb: no need to lock since this always executes on the main thread
		timediv = 1
		if time.time()-self.startTime > 60: timediv = 60
		log.info('Test progress: %s = %s of tests in %d %s', ('completed %d/%d' % (executed, self.numTests)),
				'%0.1f%%' % (100.0 * executed / self.numTests), int((time.time()-self.startTime)/timediv),
				'seconds' if timediv==1 else 'minutes', extra=ColorLogFormatter.tag(LOG_TEST_PROGRESS, [0,1]))
		failednumber = sum([self.outcomes[o] for o in OUTCOMES if o.isFailure()])
		passed = ', '.join(['%d %s'%(self.outcomes[o], o) for o in OUTCOMES if not o.isFailure() and self.outcomes[o]>0])
		failed = ', '.join(['%d %s'%(self.outcomes[o], o) for o in OUTCOMES if o.isFailure() and self.outcomes[o]>0])
		if passed: log.info('   %s (%0.1f%%)', passed, 100.0 * (executed-failednumber) / executed, extra=ColorLogFormatter.tag(LOG_PASSES))
		if failed: log.info('   %s', failed, extra=ColorLogFormatter.tag(LOG_FAILURES))
		if self._recentFailureReasons:
			log.info('Recent failures: ', extra=ColorLogFormatter.tag(LOG_TEST_PROGRESS))
			for f in self._recentFailureReasons:
				log.info('   ' + f, extra=ColorLogFormatter.tag(LOG_FAILURES))
		inprogress = list(self.inprogress)
		if self.threads>1 and inprogress:
			log.info('Currently executing: %s', ', '.join(sorted(inprogress)), extra=ColorLogFormatter.tag(LOG_TEST_PROGRESS))
		log.info('')

class ConsoleFailureAnnotationsWriter(BaseRecordResultsWriter):
	"""Writer that prints a single annotation line to stdout for each test failure, for IDEs 
	and CI providers that can highlight failures found by regular expression stdout parsing.
	
	An instance of this writer is automatically added to every project, and enables itself only 
	if the ``PYSYS_CONSOLE_FAILURE_ANNOTATIONS`` environment variable is set. 
	
	This class is designed for simple cases. If you need to output in a format that requires escaping of special 
	characters it is best to create a custom writer class. 
	"""
	
	format = ""
	"""
	The format that will be written to stdout. If not specified as a writer property in pysysproject.xml, the 
	environment variable ``PYSYS_CONSOLE_FAILURE_ANNOTATIONS`` will be used as the format. 
	
	The format can include the following placeholders:
	
		- ``@testFile@``: the absolute path to the test file (e.g. pysystest.py/run.py), using platform-specific slashes.
		- ``@testFile/@``: the absolute path to the test file, using forward slashes on all OSes.
		- ``@testFileLine@``: the line number in the test file (if available, else 0).
		- ``@runLogFile@``: the absolute path to the run log (e.g. run.log), using platform-specific slashes.
		- ``@runLogFile/@``: the absolute path to the run log (e.g. run.log), using forward slashes on all OSes.
		- ``@category@``: either ``error`` or if it's a non-failure outcome, ``warning``. 
		- ``@outcome@``: the outcome e.g. ``FAILED``.
		- ``@outcomeReason@``: the string containing the reason for the failure; this string can 
		  contain any characters (other than newline).
		- ``@testIdAndCycle@``: the test identifier, with a cycle suffix if this is a multi-cycle test.
	
	The default format if the environment variable is empty and format is not provided is `DEFAULT_FORMAT`. 
	"""
	
	DEFAULT_FORMAT = "@testFile@:@testFileLine@: @category@: @outcome@ - @outcomeReason@ (@testIdAndCycle@)"
	"""
	This is the default format if the environment variable is empty and ``format`` is not provided. 

	The output looks like this::
	
		c:\\myproject\\tests\\MyTest_001\\pysystest.py:4: error: TIMED OUT - This test timed out (MyTest_001 [CYCLE 03])
	
	which is similar to output from "make" and so should be parseable by many tools and IDEs. 
	
	"""

	includeNonFailureOutcomes = 'NOT VERIFIED'
	"""
	In addition to failure outcomes, any outcomes listed here (as comma-separated display names) will be reported 
	(with a ``@category@`` of ``warning`` rather than ``error``). 
	"""
	
	enableIfEnvironmentVariable = "PYSYS_CONSOLE_FAILURE_ANNOTATIONS"
	"""
	The environment variable used to control whether it is enabled. 
	
	This writer will be enabled if the specified environment variable is set (either to any empty string or to any 
	value other than "false"). 
	
	Set enableIfEnvironmentVariable to "" to ignore the environment and instead enable when running with ``--record``. 
	"""

	def setup(self, cycles=-1, **kwargs):
		for k in self.pluginProperties: 
			if not hasattr(type(self), k): raise UserError('Unknown property "%s" for %s'%(k, self))

		super(ConsoleFailureAnnotationsWriter, self).setup(cycles=cycles, **kwargs)
		self.cycles=cycles
		self.format = self.format or os.getenv('PYSYS_CONSOLE_FAILURE_ANNOTATIONS','') or self.DEFAULT_FORMAT
		if self.format.lower()=='true': self.format = self.DEFAULT_FORMAT
		
		self.includeNonFailureOutcomes = [o.strip().upper() for o in self.includeNonFailureOutcomes.split(',') if o.strip()]
		for o in self.includeNonFailureOutcomes:
			if not any(o == str(outcome) for outcome in OUTCOMES):
				raise UserError('Unknown outcome display name "%s" in includeNonFailureOutcomes'%o)

	def isEnabled(self, record=False, **kwargs): 
		if not self.enableIfEnvironmentVariable: return record
		
		env = os.getenv(self.enableIfEnvironmentVariable, None)
		if env is None or env.lower()=='false': return False
		return True

	def processResult(self, testObj, cycle=-1, **kwargs):
		outcome = testObj.getOutcome()
		if outcome.isFailure():
			category = 'error'
		elif str(outcome) in self.includeNonFailureOutcomes:
			category = 'warning'
		else:
			return
		
		loc = testObj.getOutcomeLocation()
		if not loc[0]: loc = (os.path.normpath(testObj.output+'/run.log'), 0) # this is a reasonable fallback
		stdoutPrint(self.format\
			.replace('@testFile@', self.escape(loc[0]))
			.replace('@testFile/@', self.escape((loc[0]).replace(os.sep,'/')))
			.replace('@testFileLine@', loc[1] or '0')
			.replace('@runLogFile@', self.escape(testObj.output+'/run.log'))
			.replace('@runLogFile/@', self.escape((testObj.output+'/run.log').replace(os.sep,'/')))
			.replace('@category@', category)
			.replace('@outcome@', str(testObj.getOutcome()))
			.replace('@outcomeReason@', self.escape(testObj.getOutcomeReason() or '(no outcome reason)'))
			.replace('@testIdAndCycle@', self.escape(testObj.descriptor.id+(' [CYCLE %02d]'%(cycle+1) if self.cycles>1 else '')))
			)
	
	def escape(self, str):
		return str.replace('\r','').replace('\n', '; ')

