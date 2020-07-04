#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
Writers are configurable plug-ins that record test outcomes (typically on disk, on the console, or to your CI tooling). 

This module contains the `BaseResultsWriter` abstract class which defines the writer API, as well as several 
sample implementations.

Output writers are responsible for summarising test results as each test completes, or at the end when all 
tests has completed. There are currently three distinct types of writers, namely 'Record', 'Progress', and
'Summary', each of which generates output at different stages of a run:

   - `BaseRecordResultsWriter`: **Record writers** output the outcome of a specific test after completion of that test, to allow
     runtime auditing of the test output, e.g. into text file, a database, or to the console in a format that 
     can be read by your Continuous Integration (CI) tooling. Several record
     writers are distributed with the PySys framework, such as the `JUnitXMLResultsWriter` and `ci.TravisCIWriter`.
     By default, record writers are enabled only when the ``--record`` flag is given to the PySys launcher, 
     though some writers may enable/disable themselves under different conditions, by overriding the 
     L{BaseResultsWriter.isEnabled} method.

   - `BaseProgressResultsWriter`: **Progress writers** output a summary of the test progress after completion of each test, to give
     an indication of how far and how well the run is progressing. A single implementation of a progress
     writer is distributed with the PySys framework, namely the L{ConsoleProgressResultsWriter},
     which details the percentage of tests selected to be run and that have executed, and a summary
     of the recent test failures. 
     Progress writers should extend the L{BaseProgressResultsWriter} and
     are enabled when the ``--progress`` flag is given to the PySys launcher, or when ``PYSYS_PROGRESS=true`` is
     set in the local environment.

   - `BaseSummaryResultsWriter`: **Summary writers** output an overall summary of the status at the end of a test run. 
     A single implementation of a summary writer is distributed with the PySys framework, namely the L{ConsoleSummaryResultsWriter},
     which details the overall test run outcome and lists any tests that did not pass. 
     Summary writers are always enabled regardless of the flags given to the PySys launcher.

Project configuration of the writers is through the PySys project XML file using the ``<writer>`` tag. Multiple
writers may be configured and their individual properties set through the nested ``<property>`` tag. Writer
properties are set as attributes to the class through the ``setattr()`` function. Custom (site specific) modules
can be created and configured by users of the PySys framework (e.g. to output test results into a relational
database etc), though they must adhere to the interface demonstrated by the implementations demonstrated here.
If no progress writers are explicitly configured in the PySys project XML file, an instance of
L{ConsoleProgressResultsWriter} is used. If no summary writer is explicitly configured in the PySys project
XML file, an instance of L{ConsoleSummaryResultsWriter} is used.

The writers are instantiated and invoked by the L{pysys.baserunner.BaseRunner} class instance. This calls the class
constructors of all configured test writers, and then the setup (prior to executing the set of tests), processResult
(process a test result), and cleanup (upon completion of the execution of all tests). The ``**kwargs`` method parameter
is used for variable argument passing in the interface methods to allow modification of the PySys framework without
breaking writer implementations already in existence.

"""

__all__ = [
	"BaseResultsWriter", "BaseRecordResultsWriter", "BaseSummaryResultsWriter", "BaseProgressResultsWriter", "ArtifactPublisher", "TestOutcomeSummaryGenerator", 
	"TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter", 
	"ConsoleSummaryResultsWriter", "ConsoleProgressResultsWriter",  "TestOutputArchiveWriter"]

import time, stat, logging, sys, io
import zipfile
if sys.version_info[0] == 2:
	from urlparse import urlunparse
else:
	from urllib.parse import urlunparse

from pysys.constants import *
from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe
from pysys.utils.pycompat import PY2

from xml.dom.minidom import getDOMImplementation

log = logging.getLogger('pysys.writer')

class BaseResultsWriter(object):
	"""Base class for all writers that get notified as and when test results are available.
	
	Writer can additionally subclass `ArtifactPublisher` to be notified of artifacts produced by other writers 
	that they wish to publish. If you are implementing a writer that needs a textual summary of the test outcomes, 
	you can add `TestOutcomeSummaryGenerator` as a superclass to get this functionality. 

	:param str logfile: Optional configuration property specifying a file to store output in. 
		Does not apply to all writers, can be ignored if not needed. 

	:param kwargs: Additional keyword arguments may be added in a future release. 
	"""

	__writerInstance = 0

	def __init__(self, logfile=None, **kwargs):
		BaseResultsWriter.__writerInstance += 1
		self.__writerRepr = 'writer#%d<%s>'%(BaseResultsWriter.__writerInstance, self.__class__.__name__)
	
	def __repr__(self): return self.__writerRepr

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
	be notified when another writer (or performance reporter) produces an artifact.
	
	To publish an artifact to all registered writers, call `pysys.baserunner.BaseRunner.publishArtifact()`. 
	
	.. versionadded:: 1.6.0
	"""

	def publishArtifact(self, path, category, **kwargs):
		"""
		Called when a file or directory artifact has been written and is ready to be published (e.g. by another writer).
		
		:param str path: Absolute path of the file or directory, using forward slashes as the path separator. 
		:param str category: A string identifying what kind of artifact this is, e.g. 
			"TestOutputArchive" and "TestOutputArchiveDir" (from `pysys.writer.TestOutputArchiveWriter`) or 
			"CSVPerformanceReport" (from `pysys.utils.perfreporter.CSVPerformanceReporter`). 
			If you create your own category, be sure to add an org/company name prefix to avoid clashes.
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

	showTestTitle = False
	"""Configures whether the summary includes the test title for each failure. """
	
	showOutcomeStats = True
	"""Configures whether the summary includes a count of the number of each outcomes."""
	
	showDuration = False
	"""Configures whether the summary includes the total duration of all tests."""
	
	showTestIdList = False
	"""Configures whether the summary includes a short list of the failing test ids in a form that's easy to paste onto the 
	command line to re-run the failed tests. """

	
	def setup(self, cycles=0, threads=0, **kwargs):
		self.results = {}
		self.startTime = time.time()
		self.duration = 0.0
		for cycle in range(cycles):
			self.results[cycle] = {}
			for outcome in PRECEDENT: self.results[cycle][outcome] = []
		self.threads = threads
		self.outcomes = {o: 0 for o in PRECEDENT}

	def processResult(self, testObj, cycle=-1, testTime=-1, testStart=-1, **kwargs):
		self.results[cycle][testObj.getOutcome()].append( (testObj.descriptor.id, testObj.getOutcomeReason(), testObj.descriptor.title, testObj.output))
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

	def logSummary(self, log, showDuration=None, showOutcomeStats=None, showOutcomeReason=None, showTestTitle=None, showOutputDir=None, showTestIdList=None, **kwargs):
		"""
		Writes a textual summary using the specified log function, with colored output if enabled.
		
		:param Callable[format,args,kwargs=] log: The function to call for each line of the summary (e.g. log.critical). 
			The message is obtained with ``format % args``, and color information is available from the ``extra=`` 
			keyword argument.
		"""
		assert not kwargs, kwargs.keys()

		if showDuration is None: showDuration = str(self.showDuration).lower() == 'true'
		if showOutcomeStats is None: showOutcomeStats = str(self.showOutcomeStats).lower() == 'true'
		if showOutcomeReason is None: showOutcomeReason = str(self.showOutcomeReason).lower() == 'true'
		if showOutputDir is None: showOutputDir = str(self.showOutputDir).lower() == 'true'
		if showTestTitle is None: showTestTitle = str(self.showTestTitle).lower() == 'true'
		if showTestIdList is None: showTestIdList = str(self.showTestIdList).lower() == 'true'

		if showDuration:
			log(  "Completed test run at:  %s", time.strftime('%A %Y-%m-%d %H:%M:%S %Z', time.localtime(time.time())), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			if self.threads > 1: 
				log("Total test duration (absolute): %s", '%.2f secs'%(time.time() - self.startTime), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
				log("Total test duration (additive): %s", '%.2f secs'%self.duration, extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			else:
				log("Total test duration:    %s", "%.2f secs"%(time.time() - self.startTime), extra=ColorLogFormatter.tag(LOG_DEBUG, 0))
			log('')		


		if showOutcomeStats:
			executed = sum(self.outcomes.values())
			failednumber = sum([self.outcomes[o] for o in FAILS])
			passed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o not in FAILS and self.outcomes[o]>0])
			failed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o in FAILS and self.outcomes[o]>0])
			if failed: log('Failure outcomes: %s (%0.1f%%)', failed, 100.0 * (failednumber) / executed, extra=ColorLogFormatter.tag(LOOKUP[FAILED].lower(), [0,1]))
			if passed: log('Success outcomes: %s', passed, extra=ColorLogFormatter.tag(LOOKUP[PASSED].lower(), [0]))
			log('')

		log("Summary of failures: ")
		fails = 0
		for cycle in self.results:
			for outcome, tests in self.results[cycle].items():
				if outcome in FAILS : fails = fails + len(tests)
		if fails == 0:
			log("	THERE WERE NO FAILURES", extra=ColorLogFormatter.tag(LOG_PASSES))
		else:
			failedids = set()
			for cycle in self.results:
				cyclestr = ''
				if len(self.results) > 1: cyclestr = '[CYCLE %d] '%(cycle+1)
				for outcome in FAILS:
					for (id, reason, testTitle, outputdir) in self.results[cycle][outcome]: 
						failedids.add(id)
						log("  %s%s: %s ", cyclestr, LOOKUP[outcome], id, extra=ColorLogFormatter.tag(LOOKUP[outcome].lower()))
						if showTestTitle and testTitle:
							log("      (title: %s)", testTitle, extra=ColorLogFormatter.tag(LOG_DEBUG))
						if showOutcomeReason and reason:
							log("      %s", reason, extra=ColorLogFormatter.tag(LOG_TEST_OUTCOMES))
						if showOutputDir:
							log("      %s", os.path.normpath(os.path.relpath(outputdir))+os.sep)
		
			if showTestIdList and len(failedids) > 1:
				# display just the ids, in a way that's easy to copy and paste into a command line
				failedids = list(failedids)
				failedids.sort()
				if len(failedids) > 20: # this feature is only useful for small test runs
					failedids = failedids[:20]+['...']
				log('')
				log('List of failed test ids:')
				log('%s', ' '.join(failedids))

class flushfile(): 
	"""Utility class to flush on each write operation - for internal use only.  
	
	:meta private:
	"""
	fp=None 
	
	def __init__(self, fp): 
		"""Create an instance of the class. 
		
		:param fp: The file object
		
		"""
		self.fp = fp
	
	def write(self, msg):
		"""Perform a write to the file object.
		
		:param msg: The string message to write. 
		
		"""
		if self.fp is not None:
			self.fp.write(msg) 
			self.fp.flush() 
	
	def seek(self, index):
		"""Perform a seek on the file objet.
		
		"""
		if self.fp is not None: self.fp.seek(index)
	
	def close(self):
		"""Close the file objet.
		
		"""
		if self.fp is not None: self.fp.close()


class TextResultsWriter(BaseRecordResultsWriter):
	"""Class to log a summary of the results to a logfile in .txt format.
	
	"""

	outputDir = None
	"""
	The directory to write the logfile, if an absolute path is not specified. The default is the working directory. 

	Project ``${...}`` properties can be used in the path. 
	"""
	
	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.fp = None

	def setup(self, **kwargs):
		# Creates the file handle to the logfile and logs initial details of the date, 
		# platform and test host. 

		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
		self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
		self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))

	def cleanup(self, **kwargs):
		# Flushes and closes the file handle to the logfile.  

		if self.fp: 
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None

	def processResult(self, testObj, **kwargs):
		# Writes the test id and outcome to the logfile. 
		
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.fp.write('\n[Cycle %d]:\n'%(self.cycle+1))
		
		self.fp.write("%s: %s\n" % (LOOKUP[testObj.getOutcome()], testObj.descriptor.id))

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

class XMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in XML format.
	
	The class creates a DOM document to represent the test output results and writes the DOM to the 
	logfile using toprettyxml(). The outputDir, stylesheet, useFileURL attributes of the class can 
	be over-ridden in the PySys project file using the nested <property> tag on the <writer> tag.
	 
	:ivar str ~.outputDir: Path to output directory to write the test summary files
	:ivar str ~.stylesheet: Path to the XSL stylesheet
	:ivar str ~.useFileURL: Indicates if full file URLs are to be used for local resource references 
	
	"""
	outputDir = None
	stylesheet = DEFAULT_STYLESHEET
	useFileURL = "false"

	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.numResults = 0
		self.fp = None

	def setup(self, **kwargs):
		# Creates the DOM for the test output summary and writes to logfile. 
						
		self.numTests = kwargs["numTests"] if "numTests" in kwargs else 0 
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile
		
		try:
			self.fp = io.open(self.logfile, "wb")
		
			impl = getDOMImplementation()
			self.document = impl.createDocument(None, "pysyslog", None)
			if self.stylesheet:
				stylesheet = self.document.createProcessingInstruction("xml-stylesheet", "href=\"%s\" type=\"text/xsl\"" % (self.stylesheet))
				self.document.insertBefore(stylesheet, self.document.childNodes[0])

			# create the root and add in the status, number of tests and number completed
			self.rootElement = self.document.documentElement
			self.statusAttribute = self.document.createAttribute("status")
			self.statusAttribute.value="running"
			self.rootElement.setAttributeNode(self.statusAttribute)

			self.completedAttribute = self.document.createAttribute("completed")
			self.completedAttribute.value="%s/%s" % (self.numResults, self.numTests)
			self.rootElement.setAttributeNode(self.completedAttribute)
	
			# add the data node
			element = self.document.createElement("timestamp")
			element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
			self.rootElement.appendChild(element)

			# add the platform node
			element = self.document.createElement("platform")
			element.appendChild(self.document.createTextNode(PLATFORM))
			self.rootElement.appendChild(element)

			# add the test host node
			element = self.document.createElement("host")
			element.appendChild(self.document.createTextNode(HOSTNAME))
			self.rootElement.appendChild(element)

			# add the test host node
			element = self.document.createElement("root")
			element.appendChild(self.document.createTextNode(self.__pathToURL(kwargs['runner'].project.root)))
			self.rootElement.appendChild(element)

			# add the extra params nodes
			element = self.document.createElement("xargs")
			if "xargs" in kwargs: 
				for key in list(kwargs["xargs"].keys()):
					childelement = self.document.createElement("xarg")
					nameAttribute = self.document.createAttribute("name")
					valueAttribute = self.document.createAttribute("value") 
					nameAttribute.value=key
					valueAttribute.value=kwargs["xargs"][key].__str__()
					childelement.setAttributeNode(nameAttribute)
					childelement.setAttributeNode(valueAttribute)
					element.appendChild(childelement)
			self.rootElement.appendChild(element)
				
			# write the file out
			self._writeXMLDocument()
			
		except Exception:
			log.info("caught %s in XMLResultsWriter: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

	def cleanup(self, **kwargs):
		# Updates the test run status in the DOM, and re-writes to logfile.

		if self.fp: 
			self.statusAttribute.value="complete"
			self._writeXMLDocument()
			self.fp.close()
			self.fp = None
			
	def processResult(self, testObj, **kwargs):
		# Adds the results node to the DOM and re-writes to logfile.
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.__createResultsNode()
		
		# create the results entry
		resultElement = self.document.createElement("result")
		nameAttribute = self.document.createAttribute("id")
		outcomeAttribute = self.document.createAttribute("outcome")  
		nameAttribute.value=testObj.descriptor.id
		outcomeAttribute.value=LOOKUP[testObj.getOutcome()]
		resultElement.setAttributeNode(nameAttribute)
		resultElement.setAttributeNode(outcomeAttribute)

		element = self.document.createElement("outcomeReason")
		element.appendChild(self.document.createTextNode( testObj.getOutcomeReason() ))
		resultElement.appendChild(element)
		
		element = self.document.createElement("timestamp")
		element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
		resultElement.appendChild(element)

		element = self.document.createElement("descriptor")
		element.appendChild(self.document.createTextNode(self.__pathToURL(testObj.descriptor.file)))
		resultElement.appendChild(element)

		element = self.document.createElement("output")
		element.appendChild(self.document.createTextNode(self.__pathToURL(testObj.output)))
		resultElement.appendChild(element)
		
		self.resultsElement.appendChild(resultElement)
	
		# update the count of completed tests
		self.numResults = self.numResults + 1
		self.completedAttribute.value="%s/%s" % (self.numResults, self.numTests)
				
		self._writeXMLDocument()

	def _writeXMLDocument(self):
		if self.fp:
			self.fp.seek(0)
			self.fp.write(self._serializeXMLDocumentToBytes(self.document))
			self.fp.flush()
		
	def _serializeXMLDocumentToBytes(self, document):
		return replaceIllegalXMLCharacters(document.toprettyxml(indent='	', encoding='utf-8', newl=os.linesep).decode('utf-8')).encode('utf-8')

	def __createResultsNode(self):
		self.resultsElement = self.document.createElement("results")
		cycleAttribute = self.document.createAttribute("cycle")
		cycleAttribute.value="%d"%(self.cycle+1)
		self.resultsElement.setAttributeNode(cycleAttribute)
		self.rootElement.appendChild(self.resultsElement)

	def __pathToURL(self, path):
		try: 
			if self.useFileURL==True or (self.useFileURL.lower() == "false"): return path
		except Exception:
			return path
		else:
			return urlunparse(["file", HOSTNAME, path.replace("\\", "/"), "","",""])

	
class JUnitXMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log test results in the widely-used Apache Ant JUnit XML format (one output file per test per cycle). 
	
	If you need to integrate with any CI provider that doesn't have built-in support (e.g. Jenkins) this standard 
	output format will usually be the easiest way to do it. 
	
	"""
	outputDir = None
	"""
	The directory to write the XML files to, as an absolute path, or relative to the testRootDir. 

	Project ``${...}`` properties can be used in the path. 
	"""
	
	def __init__(self, **kwargs):
		self.cycle = -1

	def setup(self, **kwargs):	
		# Creates the output directory for the writing of the test summary files.  

		self.outputDir = os.path.join(kwargs['runner'].project.root, 'target','pysys-reports') if not self.outputDir else self.outputDir
		deletedir(self.outputDir)
		mkdir(self.outputDir)
		self.cycles = kwargs.pop('cycles', 0)

	def processResult(self, testObj, **kwargs):
		# Creates a test summary file in the Apache Ant JUnit XML format. 
		
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
		
		impl = getDOMImplementation()		
		document = impl.createDocument(None, 'testsuite', None)		
		rootElement = document.documentElement
		attr1 = document.createAttribute('name')
		attr1.value = testObj.descriptor.id
		attr2 = document.createAttribute('tests')
		attr2.value='1'
		attr3 = document.createAttribute('failures')
		attr3.value = '%d'%(int)(testObj.getOutcome() in FAILS)	
		attr4 = document.createAttribute('skipped')	
		attr4.value = '%d'%(int)(testObj.getOutcome() == SKIPPED)		
		attr5 = document.createAttribute('time')	
		attr5.value = '%s'%kwargs['testTime']
		rootElement.setAttributeNode(attr1)
		rootElement.setAttributeNode(attr2)
		rootElement.setAttributeNode(attr3)
		rootElement.setAttributeNode(attr4)
		rootElement.setAttributeNode(attr5)
		
		# add the testcase information
		testcase = document.createElement('testcase')
		attr1 = document.createAttribute('classname')
		attr1.value = testObj.descriptor.classname
		attr2 = document.createAttribute('name')
		attr2.value = testObj.descriptor.id		   	
		testcase.setAttributeNode(attr1)
		testcase.setAttributeNode(attr2)
		
		# add in failure information if the test has failed
		if (testObj.getOutcome() in FAILS):
			failure = document.createElement('failure')
			attr1 = document.createAttribute('message')
			attr1.value = LOOKUP[testObj.getOutcome()]
			failure.setAttributeNode(attr1)
			failure.appendChild(document.createTextNode( testObj.getOutcomeReason() ))		
						
			stdout = document.createElement('system-out')
			runLogOutput = stripANSIEscapeCodes(kwargs.get('runLogOutput','')) # always unicode characters
			stdout.appendChild(document.createTextNode(runLogOutput.replace('\r','').replace('\n', os.linesep)))
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		self._writeXMLDocument(document, testObj, **kwargs)

	def _writeXMLDocument(self, document, testObj, **kwargs):
		with io.open(toLongPathSafe(os.path.join(self.outputDir,
			('TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle+1)) if self.cycles > 1 else 
			('TEST-%s.xml'%(testObj.descriptor.id)))), 
			'wb') as fp:
				fp.write(self._serializeXMLDocumentToBytes(document))

	def _serializeXMLDocumentToBytes(self, document):
		return replaceIllegalXMLCharacters(document.toprettyxml(indent='	', encoding='utf-8', newl=os.linesep).decode('utf-8')).encode('utf-8')

	def purgeDirectory(self, dir, delTop=False): # pragma: no cover
		"""
		:meta private: Deprecated, use L{pysys.utils.fileutils.deletedir} instead. 
		"""
		for file in os.listdir(dir):
			path = os.path.join(dir, file)
			if PLATFORM in ['sunos', 'linux']:
				mode = os.lstat(path)[stat.ST_MODE]
			else:
				mode = os.stat(path)[stat.ST_MODE]
		
			if stat.S_ISLNK(mode):
				os.unlink(path)
			if stat.S_ISREG(mode):
				os.remove(path)
			elif stat.S_ISDIR(mode):
				self.purgeDirectory(path, delTop=True)

		if delTop: 
			os.rmdir(dir)


class CSVResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in CSV format.

	Writing of the test summary file defaults to the working directory. This can be be over-ridden in the PySys
	project file using the nested <property> tag on the <writer> tag. The CSV column output is in the form::

		id, title, cycle, startTime, duration, outcome

	"""
	outputDir = None

	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.fp = None

	def setup(self, **kwargs):
		# Creates the file handle to the logfile and logs initial details of the date,
		# platform and test host.

		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('id, title, cycle, startTime, duration, outcome\n')

	def cleanup(self, **kwargs):
		# Flushes and closes the file handle to the logfile.
		if self.fp:
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None

	def processResult(self, testObj, **kwargs):
		# Writes the test id and outcome to the logfile.

		testStart = kwargs["testStart"] if "testStart" in kwargs else time.time()
		testTime = kwargs["testTime"] if "testTime" in kwargs else 0
		cycle = (kwargs["cycle"]+1) if "cycle" in kwargs else 0

		csv = []
		csv.append(testObj.descriptor.id)
		csv.append('\"%s\"'%testObj.descriptor.title)
		csv.append(str(cycle))
		csv.append((time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(testStart))))
		csv.append(str(testTime))
		csv.append(LOOKUP[testObj.getOutcome()])
		self.fp.write('%s \n' % ','.join(csv))

class ConsoleSummaryResultsWriter(BaseSummaryResultsWriter, TestOutcomeSummaryGenerator):
	"""Default summary writer that is used to list a summary of the test results at the end of execution.

	Support the same configuration options as `TestOutcomeSummaryGenerator`.
	"""
	# change some of the TestOutcomeSummaryGenerator defaults for the console
	showOutcomeReason = True
	showOutputDir = True
	showDuration = True
	showTestIdList = True
	
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
		self.cycles = cycles
		self.numTests = numTests
		self.startTime = time.time()

		self.outcomes = {}
		for o in PRECEDENT: self.outcomes[o] = 0
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
		
		if outcome in FAILS:
			m = LOOKUP[outcome]+': '+id
			if testObj.getOutcomeReason(): m += ': '+testObj.getOutcomeReason()
			self._recentFailureReasons.append(m)
			self._recentFailureReasons = self._recentFailureReasons[-1*self.recentFailures:] # keep last N
		
		# nb: no need to lock since this always executes on the main thread
		timediv = 1
		if time.time()-self.startTime > 60: timediv = 60
		log.info('Test progress: %s = %s of tests in %d %s', ('completed %d/%d' % (executed, self.numTests)),
				'%0.1f%%' % (100.0 * executed / self.numTests), int((time.time()-self.startTime)/timediv),
				'seconds' if timediv==1 else 'minutes', extra=ColorLogFormatter.tag(LOG_TEST_PROGRESS, [0,1]))
		failednumber = sum([self.outcomes[o] for o in FAILS])
		passed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o not in FAILS and self.outcomes[o]>0])
		failed = ', '.join(['%d %s'%(self.outcomes[o], LOOKUP[o]) for o in PRECEDENT if o in FAILS and self.outcomes[o]>0])
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

class TestOutputArchiveWriter(BaseRecordResultsWriter):
	"""Writer that creates zip archives of each failed test's output directory, 
	producing artifacts that could be uploaded to a CI system or file share to allow the failures to be analysed. 
	
	This writer is enabled when running with ``--record``. If using this writer in conjunction with a CI writer that 
	publishes the generated archives, be sure to include this writer first in the list of writers in your project 
	configuration. 

	Publishes artifacts with category name "TestOutputArchive" and the directory (unless there are no archives) 
	as "TestOutputArchiveDir" for any enabled `ArtifactPublisher` writers. 

	.. versionadded:: 1.6.0

	The following properties can be set in the project configuration for this writer:		
	"""

	destDir = '__pysys_output_archives/'
	"""
	The directory to write the archives to, as an absolute path, or relative to the testRootDir. 

	This directory will be deleted at the start of the run if it already exists. 
	
	Project ``${...}`` properties can be used in the path, and additionally the string ``@OUTDIR@`` is replaced by 
	the basename of the output directory for this test run. 
	"""
	
	maxTotalSizeMB = 1024.0
	"""
	The (approximate) limit on the total size of all archives.
	"""
	
	maxArchiveSizeMB = 200.0
	"""
	The (approximate) limit on the size each individual test archive.
	"""
	
	maxArchives = 50
	"""
	The maximum number of archives to create. 
	"""
	
	archiveAtEndOfRun = True # if at end of run can give deterministic order, also reduces I/O while tests are executing
	"""
	By default all archives are created at the end of the run once all tests have finished executing. This avoids 
	I/O contention with execution of tests, and also selection of the tests to generated archives to be done 
	in a deterministic (but pseudo-random) fashion rather than just taking the first N failures. 
	
	Alternatively you can this property to false if you wish to create archives during the test run as each failure 
	occurs. 
	"""
	
	fileExcludesRegex = u''
	"""
	A regular expression indicating test output paths that will be excluded from archiving, for example large 
	temporary files that are not useful for diagnosing problems. 
	
	For example ``".*/MyTest_001/.*/mybigfile.*[.]tmp"``.
	
	The expression is matched against the path of each output file relative to the test root dir, 
	using forward slashes as the path separator. Multiple paths can be specified using "(path1|path2)" syntax. 
	"""
	
	fileIncludesRegex = u'' # executed against the path relative to the test root dir e.g. (pattern1|pattern2)
	"""
	A regular expression indicating test output paths that will be included from archiving. This can be used to 
	archive just some particular files. Note that for use cases such as collecting graphs and code coverage files 
	generated by a test run, the collect-test-output feature is usually a better fit than using this writer. 
	
	The expression is matched against the path of each output file relative to the test root dir, 
	using forward slashes as the path separator. Multiple paths can be specified using "(path1|path2)" syntax. 
	"""
	
	def setup(self, numTests=0, cycles=1, xargs=None, threads=0, testoutdir=u'', runner=None, **kwargs):
		self.runner = runner
		if not self.destDir: raise Exception('Cannot set destDir to ""')
		self.destDir = toLongPathSafe(os.path.normpath(os.path.join(runner.project.root, self.destDir\
				.replace('@OUTDIR@', os.path.basename(runner.outsubdir)) \
				)))
		if os.path.exists(self.destDir) and all(f.endswith(('.txt', '.zip')) for f in os.listdir(self.destDir)):
			deletedir(self.destDir) # remove any existing archives (but not if this dir seems to have other stuff in it!)

		self.archiveAtEndOfRun = str(self.archiveAtEndOfRun).lower()=='true'

		self.fileExcludesRegex = re.compile(self.fileExcludesRegex) if self.fileExcludesRegex else None
		self.fileIncludesRegex = re.compile(self.fileIncludesRegex) if self.fileIncludesRegex else None

		self.maxArchiveSizeMB = float(self.maxArchiveSizeMB)
		self.maxArchives = int(self.maxArchives)
		
		self.__totalBytesRemaining = int(float(self.maxTotalSizeMB)*1024*1024)

		if self.archiveAtEndOfRun:
			self.queuedInstructions = []

		self.skippedTests = []
		self.archivesCreated = 0

	def cleanup(self, **kwargs):
		if self.archiveAtEndOfRun:
			for _, id, outputDir in sorted(self.queuedInstructions): # sort by hash of testId so make order deterministic
				self._archiveTestOutputDir(id, outputDir)
		
		if self.skippedTests:
			# if we hit a limit, at least record the names of the tests we missed
			mkdir(self.destDir)
			with io.open(self.destDir+os.sep+'skipped_artifacts.txt', 'w', encoding='utf-8') as f:
				f.write('\n'.join(os.path.normpath(t) for t in self.skippedTests))
		
		(log.info if self.archivesCreated else log.debug)('%s created %d test output archive artifacts in: %s', 
			self.__class__.__name__, self.archivesCreated, self.destDir)

		if self.archivesCreated:
			self.runner.publishArtifact(self.destDir, 'TestOutputArchiveDir')

	def shouldArchive(self, testObj, **kwargs):
		"""
		Decides whether this test is eligible for archiving of its output. 
		
		The default implementation archives only tests that have a failure outcome, 
		but this can be customized if needed by subclasses. 
		
		:param pysys.basetest.BaseTest testObj: The test object under consideration.
		:return bool: True if this test's output can be archived. 
		"""
		return testObj.getOutcome() in FAILS

	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, runLogOutput=u'', **kwargs):
		if not self.shouldArchive(testObj): return 
		
		id = ('%s.cycle%03d'%(testObj.descriptor.id, testObj.testCycle)) if testObj.testCycle else testObj.descriptor.id
		
		if self.archiveAtEndOfRun:
			self.queuedInstructions.append([hash(id), id, testObj.output])
		else:
			self._archiveTestOutputDir(id, testObj.output)
	
	def _newArchive(self, id, **kwargs):
		"""
		Creates and opens a new archive file for the specified id.
		
		:return: (str path, filehandle) The path will include an appropriate extension for this archive type. 
		  The filehandle must have the same API as Python's ZipFile class. 
		"""
		path = self.destDir+os.sep+id+'.zip'
		return path, zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True)

	def _archiveTestOutputDir(self, id, outputDir, **kwargs):
		"""
		Creates an archive for the specified test, unless doing so would violate the configured limits 
		(e.g. maxArchives). 
		
		:param str id: The testId (plus a cycle suffix if it's a multi-cycle run). 
		:param str outputDir: The path of the test output dir. 
		"""
		if self.archivesCreated == 0: mkdir(self.destDir)

		if self.archivesCreated == self.maxArchives:
			self.skippedTests.append(outputDir)
			log.debug('Skipping archiving for %s as maxArchives limit is reached', id)
			return
		if self.__totalBytesRemaining < 500:
			self.skippedTests.append(outputDir)
			log.debug('Skipping archiving for %s as maxTotalMB limit is reached', id)
			return
		self.archivesCreated += 1

		try:
			outputDir = toLongPathSafe(outputDir)
			skippedFiles = []
			
			# this is performance-critical so worth caching these
			fileExcludesRegex = self.fileExcludesRegex
			fileIncludesRegex = self.fileIncludesRegex
			isPurgableFile = self.runner.isPurgableFile
			
			bytesRemaining = min(int(self.maxArchiveSizeMB*1024*1024), self.__totalBytesRemaining)
			triedTmpZipFile = False
			
			
			zippath, myzip = self._newArchive(id)
			filesInZip = 0
			with myzip:
				rootlen = len(outputDir) + 1

				for base, dirs, files in os.walk(outputDir):
					# Just the files, don't bother with the directories for now
					
					files.sort(key=lambda fn: [fn!='run.log', fn] ) # be deterministic, and put run.log first
					
					for f in files:
						fn = os.path.join(base, f)
						if fileExcludesRegex is not None and fileExcludesRegex.search(fn.replace('\\','/')):
							skippedFiles.append(fn)
							continue
						if fileIncludesRegex is not None and not fileIncludesRegex.search(fn.replace('\\','/')):
							skippedFiles.append(fn)
							continue
						
						fileSize = os.path.getsize(fn)
						if fileSize == 0:
							# Since (if not waiting until end) this gets called before testComplete has had a chance to clean things up, skip the 
							# files that it would have deleted. Don't bother listing these in skippedFiles since user 
							# won't be expecting them anyway
							continue
						
						if bytesRemaining < 500:
							skippedFiles.append(fn)
							continue
						
						if fileSize > bytesRemaining:
							if triedTmpZipFile: # to save effort, don't keep trying once we're close - from now on only attempt small files
								skippedFiles.append(fn)
								continue
							triedTmpZipFile = True
							
							# Only way to know if it'll fit is to try compressing it
							log.debug('File size of %s might push the archive above the limit; creating a temp zip to check', fn)
							tmpname, tmpzip = self._newArchive(id+'.tmp')
							try:
								with tmpzip:
									tmpzip.write(fn, 'tmp')
									compressedSize = tmpzip.getinfo('tmp').compress_size
									if compressedSize > bytesRemaining:
										log.debug('Skipping file as compressed size of %s bytes exceeds remaining limit of %s bytes: %s', 
											compressedSize, bytesRemaining, fn)
										skippedFiles.append(fn)
										continue
							finally:
								os.remove(tmpname)
						
						memberName = fn[rootlen:].replace('\\','/')
						myzip.write(fn, memberName)
						filesInZip += 1
						bytesRemaining -= myzip.getinfo(memberName).compress_size
				
				if skippedFiles and fileIncludesRegex is None: # keep the archive clean if there's an explicit include
					myzip.writestr('__pysys_skipped_archive_files.txt', os.linesep.join([fromLongPathSafe(f) for f in skippedFiles]).encode('utf-8'))
	
			if filesInZip == 0:
				# don't leave empty zips around
				log.debug('No files added to zip so deleting: %s', zippath)
				self.archivesCreated -= 1
				os.remove(zippath)
				return
	
			self.__totalBytesRemaining -= os.path.getsize(zippath)
			self.runner.publishArtifact(zippath, 'TestOutputArchive')
	
		except Exception:
			self.skippedTests.append(outputDir)
			raise
		
		