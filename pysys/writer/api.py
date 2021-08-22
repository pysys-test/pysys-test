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
API for creating new writers. 

Writers are responsible for summarising test results or processing test output as each test completes, or at the end 
when all tests has completed. 

The most common type of writer is the standard 'Record' writer, but there are also 'Progress', and
'Summary' writers which do their things at different stages of the test run:

   - `BaseRecordResultsWriter`: **Record writers** record the outcome or output of tests, allowing 
     runtime auditing of the test output, e.g. into text file, a database, or to the console in a format that 
     can be read by your Continuous Integration (CI) tooling, or collection/archiving of test output files. 
     
     Several record writers are distributed with the PySys framework, such as the 
     `pysys.writer.outcomes.JUnitXMLResultsWriter` and `pysys.writer.ci.GitHubActionsCIWriter`.
     By default, record writers are enabled only when the ``--record`` flag is given to the PySys launcher, 
     though some writers may enable/disable themselves under different conditions, by overriding the 
     L{BaseResultsWriter.isEnabled} method.

   - `BaseProgressResultsWriter`: **Progress writers** output a summary of the test progress after completion of each test, to give
     an indication of how far and how well the run is progressing. A single implementation of a progress
     writer is distributed with the PySys framework, namely the `pysys.writer.console.ConsoleProgressResultsWriter`,
     which details the percentage of tests selected to be run and that have executed, and a summary
     of the recent test failures. 
     Progress writers should extend the `BaseProgressResultsWriter` and
     are enabled when the ``--progress`` flag is given to the PySys launcher, or when ``PYSYS_PROGRESS=true`` is
     set in the local environment.

   - `BaseSummaryResultsWriter`: **Summary writers** output an overall summary of the status at the end of a test run. 
     A single implementation of a summary writer is distributed with the PySys framework, namely the 
     `pysys.writer.console.ConsoleSummaryResultsWriter`, which details the overall test run outcome and lists any tests 
     that did not pass. 
     Summary writers are always enabled regardless of the flags given to the PySys launcher.

Project configuration of the writers is through the PySys project XML file using the ``<writer>`` tag. Multiple
writers may be configured and their individual properties set through the nested ``<property>`` tag. Writer
properties are set as attributes to the writer instance just before setup is called, with automatic conversion of 
type to match the default value if specified as a static attribute on the class. 

The writers are instantiated and invoked by the L{pysys.baserunner.BaseRunner} class instance. This calls the class
constructors of all configured test writers, and then the setup (prior to executing the set of tests), processResult
(process a test result), and cleanup (upon completion of the execution of all tests). The ``**kwargs`` method parameter
should always be included in the signature of each method, to allow for future additions to PySys without
breaking existing writer implementations.

Writers that generate output files/directories should by default put that output under either the 
`runner.output <pysys.baserunner.BaseRunner>` directory, or (for increased prominence) the ``runner.output+'/..'`` 
directory (which is typically ``testRootDir`` unless an absolute ``--outdir`` path was provided) . 
A prefix of double underscore ``__pysys`` is recommended to distinguish dynamically created directories 
(ignored by version control) from the testcase directories (checked into version control). 

Writer authors may wish to make use of these helpers:

	.. autosummary::
		replaceIllegalXMLCharacters
		pysys.utils.logutils.stripANSIEscapeCodes
		pysys.utils.logutils.stdoutPrint
		pysys.utils.logutils.ColorLogFormatter

"""

__all__ = [
	"BaseResultsWriter", "BaseRecordResultsWriter", "BaseSummaryResultsWriter", "BaseProgressResultsWriter", 
	"ArtifactPublisher", "TestOutputVisitor","TestOutcomeSummaryGenerator", 
	"replaceIllegalXMLCharacters",
]

import time, stat, logging, sys, io
import locale
import shutil
import shlex

from pysys.constants import *
from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes, stdoutPrint
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2, openfile
from pysys.exceptions import UserError

log = logging.getLogger('pysys.writer')

class BaseResultsWriter(object):
	"""Base class for all writers that get notified as and when test results are available.
	
	Writer can additionally subclass `ArtifactPublisher` to be notified of artifacts produced by other writers 
	that they wish to publish, or `TestOutputVisitor` to be notified of each file in the test output directory. If you 
	are implementing a writer that needs a textual summary of the test outcomes, 
	you can add `TestOutcomeSummaryGenerator` as a superclass to get this functionality. 

	:param str logfile: Optional configuration property specifying a file to store output in. 
		Does not apply to all writers, can be ignored if not needed. 

	:param kwargs: Additional keyword arguments may be added in a future release. 
	"""

	__writerInstance = 0

	def __init__(self, logfile=None, **kwargs):
		BaseResultsWriter.__writerInstance += 1
		self.__writerRepr = 'writer#%d<%s>'%(BaseResultsWriter.__writerInstance, self.__class__.__name__)
	
	def __repr__(self): return getattr(self, '__writerRepr', self.__class__.__name__)

	def isEnabled(self, record=False, **kwargs): 
		""" Determines whether this writer can be used in the current environment. 
		
		If set to False then after construction none of the other methods 
		(including L{setup})) will be called. 
		
		:param record: True if the user ran PySys with the `--record` flag, 
			indicating that test results should be recorded. 
		 
		:return: For record writers, the default to enable only if record==True, 
			but individual writers can use different criteria if desired, e.g. 
			writers for logging output to a CI system may enable themselves 
			based on environment variables indicating that system is present, 
			even if record is not specified explicitly. 
			
		"""
		return record == True

	def setup(self, numTests=0, cycles=1, xargs=None, threads=0, testoutdir=u'', runner=None, **kwargs):
		""" Called before any tests begin. 
		
		Before this method is called, for each property "PROP" specified for this 
		writer in the project configuration file, the configured value will be 
		assigned to `self.PROP`. 

		:param numTests: The total number of tests (cycles*testids) to be executed
		:param cycles: The number of cycles. 
		:param xargs: The runner's xargs
		:param threads: The number of threads used for running tests. 
		
		:param testoutdir: The output directory used for this test run 
			(equal to `runner.outsubdir`), an identifying string which often contains 
			the platform, or when there are multiple test runs on the same machine 
			may be used to distinguish between them. This is usually a relative path 
			but may be an absolute path. 
		
		:param runner: The runner instance that owns this writer. The default implementation of this methods sets 
			the ``self.runner`` attribute to this value. 
		
		:param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		if runner is not None: self.runner = runner

	def cleanup(self, **kwargs):
		""" Called after all tests have finished executing (or been cancelled). 
		
		This is where file headers can be written, and open handles should be closed. 

		:param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass

	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, runLogOutput=u'', **kwargs):
		""" Called when each test has completed. 
		
		This method is always invoked under a lock that prevents multiple concurrent invocations so additional 
		locking is not usually necessary.  

		:param pysys.basetest.BaseTest testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. 
			The writer can extract data from this object but should not store a reference to it. 
			The ``testObj.descriptor.id`` indicates the test that ran. 
		:param int cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		:param float testTime: Duration of the test in seconds as a floating point number. 
		:param float testStart: The time when the test started. 
		:param str runLogOutput: The logging output written to the console/run.log, as a unicode character string. This 
			string will include ANSI escape codes if colored output is enabled; if desired these can be removed using 
			`pysys.utils.logutils.stripANSIEscapeCodes()`.
		:param kwargs: Additional keyword arguments may be added in future releases. 

		"""
		pass

	def processTestStarting(self, testObj, cycle=-1, **kwargs):
		""" Called when a test is just about to begin executing. 

		Note on thread-safety: unlike the other methods on this interface, this is usually executed on a
		worker thread, so any data structures accessed in this method and others on this class must be
		synchronized if performing non-atomic operations.
		
		:param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. The writer 
			can extract data from this object but should not store a reference to it. The testObj.descriptor.id
			indicates the test that ran.
		:param cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		:param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass


class BaseRecordResultsWriter(BaseResultsWriter):
	"""Base class for writers that record the results of tests, and are enabled only when the ``--record`` flag is specified.
	
	For compatibility reasons writers that do not subclass BaseSummaryResultsWriter or BaseProgressResultsWriter are
	treated as "record" writers even if they do not inherit from this class.

	"""
	pass


class BaseSummaryResultsWriter(BaseResultsWriter):
	"""Base class for writers that display a summary of test results.
	
	Summary writers are always enabled (regardless of whether ``--progress`` or ``--record`` are specified). If
	no "summary" writers are configured, a default ConsoleSummaryResultsWriter instance will be added
	automatically.

	Summary writers are invoked after all other writers, ensuring that their output 
	will be displayed after output from any other writer types. 
	"""
	def isEnabled(self, record=False, **kwargs): 
		return True # regardless of record flag


class BaseProgressResultsWriter(BaseResultsWriter):
	""" Base class for writers that display progress information while tests are running.

	Progress writers are only enabled if the ``--progress`` flag is specified.

	"""
	def isEnabled(self, record=False, **kwargs): 
		return True # regardless of record flag


class ArtifactPublisher(object):
	"""Interface implemented by writers that implement publishing of file/directory artifacts. 
	
	For example, a writer for a CI provider that supports artifact uploading can subclass this interface to 
	be notified when another writer (or performance reporter) produces an artifact. If implementing this interface, 
	remember that the order each writer's cleanup() is called is the same as the order the writers appear in the 
	project configuration file, so if your writer relies on output published from another's cleanup you may need to 
	document this, or code your writer such that it doesn't care what order the cleanup() methods are called. 
	
	To publish an artifact to all registered writers, call `pysys.baserunner.BaseRunner.publishArtifact()`. 
	
	It is possible to restrict artifact publishing to just the categories you care about by setting the 
	project property ``publishArtifactCategoryIncludeRegex`` which (if specified) must match the category name 
	in order for writers to be notified. 
	
	.. versionadded:: 1.6.0
	"""

	def publishArtifact(self, path, category, **kwargs):
		"""
		Called when a file or directory artifact has been written and is ready to be published (e.g. by another writer).
		
		:param str path: Absolute path of the file or directory, using forward slashes as the path separator. 
		:param str category: A string identifying what kind of artifact this is, e.g. 
			"TestOutputArchive" and "TestOutputArchiveDir" (from `pysys.writer.testoutput.TestOutputArchiveWriter`) or 
			"CSVPerformanceReport" (from `pysys.utils.perfreporter.CSVPerformanceReporter`). 
			If you create your own category, be sure to add an org/company name prefix to avoid clashes.
		"""
		pass


class TestOutputVisitor(object):
	"""Interface implemented by writers that wish to be notified of each file in the test output directory. 
	
	Implementing this interface is a lot more efficient than explicitly walking the directory tree. 
	Note that in the interests of performance empty (zero byte) files are ignored. 
	
	.. versionadded:: 1.6.0
	"""

	def visitTestOutputFile(self, testObj, path, **kwargs):
		r"""
		Called after execution of each test (and before purging of files) for each file found in the output 
		directory. 
		
		:param pysys.basetest.BaseTest testObj: The test object, which can be used to find the outcome etc. 
		:param str: The absolute, normalize path to the output file (will be a \\?\ long path safe path on windows). 
		:return bool: Return True if this visitor has handled this file fully (e.g. by deleting it) and it should not be 
			passed on to any other registered visitors. 
		
		"""
		pass

class TestOutcomeSummaryGenerator(BaseResultsWriter):
	"""Mix-in helper class that can be inherited by any writer to allow (configurable) generation of a textual 
	summary of the test outcomes. 

	If subclasses provide their own implementation of `setup` and `processResult` they must ensure this class's 
	methods of those names are also called. Then the summary can be obtained from `logSummary` or `getSummaryText`, 
	typically in the writer's `cleanup` method. 
	"""
	
	showOutcomeReason = True
	"""Configures whether the summary includes the reason for each failure."""
	
	showOutputDir = True
	"""Configures whether the summary includes the (relative) path to the output directory for each failure. """

	showTestDir = True
	"""Configures whether the summary includes the (relative) path to the test directory for each failure, 
	unless the output dir is displayed and the test dir is a parent of it. 
	This is useful if you run tests with an absolute --outdir. """

	showTestTitle = False
	"""Configures whether the summary includes the test title for each failure. """
	
	showOutcomeStats = True
	"""Configures whether the summary includes a count of the number of each outcomes."""
	
	showDuration = False
	"""Configures whether the summary includes the total duration of all tests."""

	showRunDetails = False
	"""Configures whether the summary includes the ``runDetails`` from the `pysys.baserunner.BaseRunner`, 
	such as ``outDirName`` and ``hostname``."""

	showInspectSummary = True
	"""Configures whether the summary includes a summary of INSPECT outcomes (if any). 	
	"""
	
	showNotVerifiedSummary = True
	"""Configures whether the summary includes a summary of NOTVERIFIED outcomes (if any). 	
	"""
	
	showTestIdList = False
	"""Configures whether the summary includes a short list of the failing test ids in a form that's easy to paste onto the 
	command line to re-run the failed tests. """

	
	def setup(self, cycles=0, threads=0, **kwargs):
		super(TestOutcomeSummaryGenerator, self).setup(cycles=cycles, threads=threads, **kwargs)

		self.results = {}
		self.startTime = time.time()
		self.duration = 0.0
		for cycle in range(cycles):
			self.results[cycle] = {}
			for outcome in OUTCOMES: self.results[cycle][outcome] = []
		self.threads = threads
		self.outcomes = {o: 0 for o in OUTCOMES}
		self.numTests = kwargs['numTests']

	def processResult(self, testObj, cycle=-1, testTime=-1, testStart=-1, **kwargs):
		self.results[cycle][testObj.getOutcome()].append( (testObj.descriptor.id, testObj.getOutcomeReason(), testObj.descriptor.title, testObj.descriptor.testDir, testObj.output))
		self.outcomes[testObj.getOutcome()] += 1
		self.duration = self.duration + testTime

	def getSummaryText(self, **kwargs):
		"""
		Get the textual summary as a single string (with no coloring). 
		
		To customize what is included in the summary (rather than letting it be user-configurable), 
		use the keyword arguments as for `logSummary`. 
		
		:return str: The summary as a string. 
		"""
		result = []
		def log(fmt, *args, **kwargs):
			result.append(fmt%args)
		self.logSummary(log=log, **kwargs)
		return '\n'.join(result)

	def logSummary(self, log, showDuration=None, showOutcomeStats=None, showTestIdList=None, showFailureSummary=True, showRunDetails=None, **kwargs):
		"""
		Writes a textual summary using the specified log function, with colored output if enabled.
		
		The keyword arguments can be used to disable sections of the output (overriding the settings) if needed by 
		the caller. 
		
		:param Callable[format,args,kwargs=] log: The function to call for each line of the summary (e.g. log.critical). 
			The message is obtained with ``format % args``, and color information is available from the ``extra=`` 
			keyword argument.
		"""
		assert not kwargs, kwargs.keys()

		if showDuration is None: showDuration = self.showDuration and self.numTests>1
		if showOutcomeStats is None: showOutcomeStats = self.showOutcomeStats and self.numTests>1
		if showTestIdList is None: showTestIdList = self.showTestIdList and self.numTests>1
		if showRunDetails is None: showRunDetails = self.showRunDetails and self.numTests>1
		
		# details from showFailureSummary:
		showOutcomeReason = self.showOutcomeReason
		showOutputDir = self.showOutputDir
		showTestDir = self.showTestDir
		showTestTitle = self.showTestTitle

		showInspectSummary = self.showInspectSummary
		showNotVerifiedSummary = self.showNotVerifiedSummary

		if showDuration:
			log(  "Completed test run at:  %s", time.strftime('%A %Y-%m-%d %H:%M:%S %Z', time.localtime(time.time())), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			if self.threads > 1: 
				log("Total test duration (absolute): %s", '%.2f secs'%(time.time() - self.startTime), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
				log("Total test duration (additive): %s", '%.2f secs'%self.duration, extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			else:
				log("Total test duration:    %s", "%.2f secs"%(time.time() - self.startTime), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			log('')		

		if showRunDetails:
			log("Run details:")
			for k, v in self.runner.runDetails.items():
				log(" %23s%s", k+': ', v, extra=ColorLogFormatter.tag(LOG_TEST_DETAILS, 1))
			log("")

		if showOutcomeStats:
			executed = sum(self.outcomes.values())
			failednumber = sum([self.outcomes[o] for o in OUTCOMES if o.isFailure()])
			passed = ', '.join(['%d %s'%(self.outcomes[o], o) for o in OUTCOMES if not o.isFailure() and self.outcomes[o]>0])
			failed = ', '.join(['%d %s'%(self.outcomes[o], o) for o in OUTCOMES if o.isFailure() and self.outcomes[o]>0])
			if failed: log('Failure outcomes: %s (%0.1f%%)', failed, 100.0 * (failednumber) / executed, extra=ColorLogFormatter.tag(str(FAILED).lower(), [0]))
			if passed: log('Success outcomes: %s', passed, extra=ColorLogFormatter.tag(str(PASSED).lower(), [0]))
			log('')

		def logForOutcome(decider):
			for cycle in self.results:
				cyclestr = ''
				if len(self.results) > 1: cyclestr = '[CYCLE %d] '%(cycle+1)
				for outcome in OUTCOMES:
					if not decider(outcome): continue
					
					# sort similar outcomes together to make the results easier to read; by reason then testDir
					self.results[cycle][outcome].sort(key=lambda test: [test[1], test[3]])
					
					for (id, reason, testTitle, testDir, outputdir) in self.results[cycle][outcome]: 
						log("  %s%s: %s ", cyclestr, outcome, id, extra=ColorLogFormatter.tag(str(outcome).lower()))
						if showTestTitle and testTitle:
							log("      (title: %s)", testTitle, extra=ColorLogFormatter.tag(LOG_DEBUG))
						if showOutcomeReason and reason:
							log("      %s", reason, extra=ColorLogFormatter.tag(LOG_TEST_OUTCOMES))
							
						try:
							outputdir = os.path.normpath(os.path.relpath(fromLongPathSafe(outputdir)))+os.sep
							testDir = os.path.normpath(os.path.relpath(fromLongPathSafe(testDir)))+os.sep
						except Exception as ex: # relpath can fail if on different Windows drives
							logging.getLogger('pysys.writer').debug('Failed to generate relative paths for "%s" and "%s": %s', outputdir, testDir, ex)
							
						if showTestDir and not (showOutputDir and outputdir.startswith(testDir)):
							# don't confuse things by showing the testDir unless its information is not present in the outputDir (due to --outdir)
							log("      %s", testDir)
						if showOutputDir:
							log("      %s", outputdir)

		if showNotVerifiedSummary and self.outcomes[NOTVERIFIED] > 0:
			log("Summary of not verified outcomes:")
			logForOutcome(lambda outcome: outcome == NOTVERIFIED)
			log('')

		if showInspectSummary and self.outcomes[INSPECT] > 0:
			log("Summary of inspect outcomes: ")
			logForOutcome(lambda outcome: outcome == INSPECT)
			log('')

		if showFailureSummary:
			log("Summary of failures: ")
			fails = 0
			for cycle in self.results:
				for outcome, tests in self.results[cycle].items():
					if outcome.isFailure(): fails = fails + len(tests)
			if fails == 0:
				log("	THERE WERE NO FAILURES", extra=ColorLogFormatter.tag(LOG_PASSES))
			else:
				logForOutcome(lambda outcome: outcome.isFailure())
			log('')

		if showTestIdList:
			failedids = []
			failedidsAlreadyDone = set()
			for cycle in self.results:
				for outcome in OUTCOMES:
					if not outcome.isFailure(): continue
					
					for (id, reason, testTitle, testDir, outputdir) in self.results[cycle][outcome]: 
						if id in failedidsAlreadyDone: continue
						failedidsAlreadyDone.add(id)
						failedids.append(id)

			if len(failedids) > 1:
				# display just the ids, in a way that's easy to copy and paste into a command line; 
				# for maximum usability, use the sort order given above
				failedids = failedids
				if len(failedids) > 100: # this feature is only useful for small test runs
					failedids = failedids[:100]+['...']
				log('List of failed test ids:')
				log('%s', ' '.join(failedids))

def replaceIllegalXMLCharacters(unicodeString, replaceWith=u'?'):
	"""
	Utility function that takes a unicode character string and replaces all characters 
	that are not permitted to appear in an XML document. 
	
	The XML specification says Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
	
	Currently Python's XML libraries do not perform checking or removal of such 
	characters, so if this function is not used then they may generate XML documents 
	that no XML API (including Python's) can read. 
	
	See https://bugs.python.org/issue5166
	
	:param unicodeString: a unicode character string (not a byte string). 
		Since most XML documents are encoded in utf-8, typical usage would be to 
		decode the UTF-8 bytes into characters before calling this function and then 
		re-encode as UTF-8 again afterwards.
	
	:param replaceWith: the unicode character string to replace each illegal character with. 
	"""
	return re.sub(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', replaceWith, unicodeString)
