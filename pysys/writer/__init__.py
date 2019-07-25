#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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
Contains API and sample implementations of L{BaseResultsWriter} and 
its subclasses, which are used to output test results during runtime execution.

Output writers are responsible for summarising test results on completion of a test, or on completion
of a set of tests. There are currently three distinct types of writers, namely `Record`, `Progress`, and
`Summary`, each of which performs output at different stages of a run:

   - `Record` writers output the outcome of a specific test after completion of that test, to allow
     runtime auditing of the test output, e.g. into a relational database. Several record
     writers are distributed with the PySys framework, such as the L{writer.JUnitXMLResultsWriter}.
     Best practice is to subclass L{writer.BaseRecordResultsWriter} when writing new record writers. 
     By default, record writers are enabled only when the --record flag is given to the PySys launcher, 
     though some writers may enable/disable themselves under different conditions, by overriding the 
     L{pysys.writer.BaseRecordResultsWriter.isEnabled} method.

   - `Progress` writers output a summary of the test progress after completion of each test, to give
     an indication of how far and how well the run is progressing. A single implementation of a progress
     writer is distributed with the PySys framework, namely the L{writer.ConsoleProgressResultsWriter},
     which details the percentage of tests selected to be run and that have executed, and a summary
     of the recent test failures. Progress writers should extend the L{writer.BaseProgressResultsWriter} and
     are enabled when the --progress flag is given to the PySys launcher, or when PYSYS_PROGRESS=true is
     set in the local environment.

   - `Summary` writers output an overall summary of the status at the end of a test run. A single implementation
     of a progress writer is distributed with the PySys framework, namely the L{writer.ConsoleSummaryResultsWriter},
     which details the overall test run outcome and lists any tests that did not pass. A summary writer is always
     enabled regardless of the flags given to the pysys launcher.

Project configuration of the writers is through the PySys project XML file using the <writer> tag. Multiple
writers may be configured and their individual properties set through the nested <property> tag. Writer
properties are set as attributes to the class through the setattr() function. Custom (site specific) modules
can be created and configured by users of the PySys framework (e.g. to output test results into a relational
database etc), though they must adhere to the interface demonstrated by the implementations demonstrated here.
If no progress writers are explicitly configured in the PySys project XML file, an instance of
L{writer.ConsoleProgressResultsWriter} is used. If no summary writer is explicitly configured in the PySys project
XML file, an instance of L{writer.ConsoleSummaryResultsWriter} is used.

The writers are instantiated and invoked by the L{pysys.baserunner.BaseRunner} class instance. This calls the class
constructors of all configured test writers, and then the setup (prior to executing the set of tests), processResult
(process a test result), and cleanup (upon completion of the execution of all tests). The **kwargs method parameter
is used for variable argument passing in the interface methods to allow modification of the PySys framework without
breaking writer implementations already in existence.

"""

__all__ = ["BaseResultsWriter", "BaseRecordResultsWriter", "BaseSummaryResultsWriter", "BaseProgressResultsWriter", "TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter", "ConsoleSummaryResultsWriter", "ConsoleProgressResultsWriter"]

import time, stat, logging, sys, io
if sys.version_info[0] == 2:
	from urlparse import urlunparse
else:
	from urllib.parse import urlunparse

from pysys.constants import *
from pysys.utils.logutils import ColorLogFormatter
from pysys.utils.fileutils import mkdir, deletedir
from pysys.utils.pycompat import PY2

from xml.dom.minidom import getDOMImplementation

log = logging.getLogger('pysys.writer')

class BaseResultsWriter(object):
	"""Base class for objects that get notified as and when test results are available. """

	def __init__(self, logfile=None, **kwargs):
		""" Create an instance of the BaseResultsWriter class.

		@param logfile: Optional configuration property specifying a file to store output in. 
		Does not apply to all writers, can be ignored if not needed. 

		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass

	def isEnabled(self, record=False, **kwargs): 
		""" Determines whether this writer can be used in the current environment. 
		
		If set to False then after construction none of the other methods 
		(including L{setup})) will be called. 
		
		@param record: True if the user ran PySys with the `--record` flag, 
		indicating that test results should be recorded. 
		 
		@returns: For record writers, the default to enable only if record==True, 
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

		@param numTests: The total number of tests (cycles*testids) to be executed
		@param cycles: The number of cycles. 
		@param xargs: The runner's xargs
		@param threads: The number of threads used for running tests. 
		
		@param testoutdir: The output directory used for this test run 
		(equal to `runner.outsubdir`), an identifying string which often contains 
		the platform, or when there are multiple test runs on the same machine 
		may be used to distinguish between them. This is usually a relative path 
		but may be an absolute path. 
		
		@param runner: The runner instance that owns this writer. 
		
		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass

	def cleanup(self, **kwargs):
		""" Called after all tests have finished executing (or been cancelled). 
		
		This is where file headers can be written, and open handles should be closed. 

		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass

	def processResult(self, testObj, cycle=0, testTime=0, testStart=0, runLogOutput=u'', **kwargs):
		""" Called when each test has completed. 
		
		This method is always invoked from the same thread as setup() and cleanup(), even 
		when multiple tests are running in parallel. 

		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. The writer 
		can extract data from this object but should not store a reference to it. 
		The testObj.descriptor.id indicates the test that ran. 
		@param cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		@param testTime: Duration of the test in seconds as a floating point number. 
		@param testStart: The time when the test started. 
		@param runLogOutput: The logging output written to run.log, as a unicode character string. 
		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass

	def processTestStarting(self, testObj, cycle=-1, **kwargs):
		""" Called when a test is just about to begin executing. 

		Note on thread-safety: unlike the other methods on this interface, this is usually executed on a
		worker thread, so any data structures accessed in this method and others on this class must be
		synchronized if performing non-atomic operations.
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class. The writer 
		can extract data from this object but should not store a reference to it. The testObj.descriptor.id
		indicates the test that ran.
		@param cycle: The cycle number. These start from 0, so please add 1 to this value before using. 
		@param kwargs: Additional keyword arguments may be added in a future release. 

		"""
		pass


class BaseRecordResultsWriter(BaseResultsWriter):
	"""Base class for writers that record the results of tests, and are enabled only when the --record flag is specified.
	
	For compatibility reasons writers that do not subclass BaseSummaryResultsWriter or BaseProgressResultsWriter are
	treated as "record" writers even if they do not inherit from this class.

	"""
	pass


class BaseSummaryResultsWriter(BaseResultsWriter):
	"""Base class for writers that display a summary of test results.
	
	Summary writers are always enabled (regardless of whether --progress or --record are specified). If
	no "summary" writers are configured, a default ConsoleSummaryResultsWriter instance will be added
	automatically.

	Summary writers are invoked after all other writers, ensuring that their output 
	will be displayed after output from any other writer types. 
	"""
	def isEnabled(self, record=False, **kwargs): 
		return True # regardless of record flag


class BaseProgressResultsWriter(BaseResultsWriter):
	""" Base class for writers that display progress information while tests are running.

	Progress writers are only enabled if the --progress flag is specified.

	"""
	def isEnabled(self, record=False, **kwargs): 
		return True # regardless of record flag

class flushfile(): 
	"""Utility class to flush on each write operation - for internal use only.  
	
	"""
	fp=None 
	
	def __init__(self, fp): 
		"""Create an instance of the class. 
		
		@param fp: The file object
		
		"""
		self.fp = fp
	
	def write(self, msg):
		"""Perform a write to the file object.
		
		@param msg: The string message to write. 
		
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
	"""Class to log results to logfile in text format.
	
	Writing of the test summary file defaults to the working directory. This can be be overridden in the PySys 
	project file using the nested <property> tag on the <writer> tag.
	 
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.fp = None

	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the file handle to the logfile and logs initial details of the date, 
		platform and test host. 
				
		@param kwargs: Variable argument list
		
		"""		
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
		self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
		self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))

	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 
		
		Flushes and closes the file handle to the logfile.  

		@param kwargs: Variable argument list
				
		"""
		if self.fp: 
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None

	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Writes the test id and outcome to the logfile. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""
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
	
	@param unicodeString: a unicode character string (not a byte string). 
	Since most XML documents are encoded in utf-8, typical usage would be to 
	decode the UTF-8 bytes into characters before calling this function and then 
	re-encode as UTF-8 again afterwards.
	
	@param replaceWith: the unicode character string to replace each illegal character with. 
	"""
	return re.sub(u'[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]', replaceWith, unicodeString)

class XMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in XML format.
	
	The class creates a DOM document to represent the test output results and writes the DOM to the 
	logfile using toprettyxml(). The outputDir, stylesheet, useFileURL attributes of the class can 
	be over-ridden in the PySys project file using the nested <property> tag on the <writer> tag.
	 
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	@ivar stylesheet: Path to the XSL stylesheet
	@type stylesheet: string
	@ivar useFileURL: Indicates if full file URLs are to be used for local resource references 
	@type useFileURL: string (true | false)
	
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
		"""Implementation of the setup method.

		Creates the DOM for the test output summary and writes to logfile. 
						
		@param kwargs: Variable argument list
		
		"""
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
		"""Implementation of the cleanup method. 
		
		Updates the test run status in the DOM, and re-writes to logfile.

		@param kwargs: Variable argument list
				
		"""
		if self.fp: 
			self.statusAttribute.value="complete"
			self._writeXMLDocument()
			self.fp.close()
			self.fp = None
			
	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Adds the results node to the DOM and re-writes to logfile.
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
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
			if self.useFileURL.lower() == "false": return path
		except Exception:
			return path
		else:
			return urlunparse(["file", HOSTNAME, path.replace("\\", "/"), "","",""])

	
class JUnitXMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log test results in Apache Ant JUnit XML format (one output file per test per cycle). 
	
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, **kwargs):
		self.cycle = -1

	def setup(self, **kwargs):	
		"""Implementation of the setup method.

		Creates the output directory for the writing of the test summary files.  
						
		@param kwargs: Variable argument list
		
		"""
		self.outputDir = os.path.join(kwargs['runner'].project.root, 'target','pysys-reports') if not self.outputDir else self.outputDir
		deletedir(self.outputDir)
		mkdir(self.outputDir)
		self.cycles = kwargs.pop('cycles', 0)

	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 

		@param kwargs: Variable argument list
				
		"""
		pass

	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Creates a test summary file in the Apache Ant JUnit XML format. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
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
			runLogOutput = kwargs.get('runLogOutput','') # always unicode characters
			stdout.appendChild(document.createTextNode(runLogOutput.replace('\r','').replace('\n', os.linesep)))
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		self._writeXMLDocument(document, testObj, **kwargs)

	def _writeXMLDocument(self, document, testObj, **kwargs):
		with io.open(os.path.join(self.outputDir,
			('TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle+1)) if self.cycles > 1 else 
			('TEST-%s.xml'%(testObj.descriptor.id))), 
			'wb') as fp:
				fp.write(self._serializeXMLDocumentToBytes(document))

	def _serializeXMLDocumentToBytes(self, document):
		return replaceIllegalXMLCharacters(document.toprettyxml(indent='	', encoding='utf-8', newl=os.linesep).decode('utf-8')).encode('utf-8')

	def purgeDirectory(self, dir, delTop=False): # pragma: no cover
		"""
		@deprecated: Use L{pysys.utils.fileutils.deletedir} instead. 
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
	project file using the nested <property> tag on the <writer> tag. The CSV column output is in the form;

	id, title, cycle, startTime, duration, outcome

	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string

	"""
	outputDir = None

	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.fp = None

	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the file handle to the logfile and logs initial details of the date,
		platform and test host.

		@param kwargs: Variable argument list

		"""
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		self.fp = flushfile(open(self.logfile, "w"))
		self.fp.write('id, title, cycle, startTime, duration, outcome\n')

	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method.

		Flushes and closes the file handle to the logfile.

		@param kwargs: Variable argument list

		"""
		if self.fp:
			self.fp.write('\n\n\n')
			self.fp.close()
			self.fp = None

	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method.

		Writes the test id and outcome to the logfile.

		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list

		"""
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


class ConsoleSummaryResultsWriter(BaseSummaryResultsWriter):
	"""Default summary writer that is used to list a summary of the test results at the end of execution.

	"""
	def __init__(self, **kwargs):
		self.showOutcomeReason = self.showOutputDir = False # option added in 1.3.0. May soon change the default to True. 
		self.showTestIdList = True
	
	def setup(self, cycles=0, threads=0, **kwargs):
		self.results = {}
		self.startTime = time.time()
		self.duration = 0.0
		for cycle in range(cycles):
			self.results[cycle] = {}
			for outcome in PRECEDENT: self.results[cycle][outcome] = []
		self.threads = threads

	def processResult(self, testObj, cycle=-1, testTime=-1, testStart=-1, **kwargs):
		self.results[cycle][testObj.getOutcome()].append( (testObj.descriptor.id, testObj.getOutcomeReason(), testObj.output ))
		self.duration = self.duration + testTime

	def cleanup(self, **kwargs):
		log = logging.getLogger('pysys.resultssummary')
		log.critical("")
		log.critical(  "Completed test run at:  %s", time.strftime('%A %Y-%m-%d %H:%M:%S %Z', time.localtime(time.time())))
		if self.threads > 1: 
			log.critical("Total test duration (absolute): %.2f secs", time.time() - self.startTime)		
			log.critical("Total test duration (additive): %.2f secs", self.duration)
		else:
			log.critical("Total test duration:    %.2f secs", time.time() - self.startTime)		
		log.critical("")		
		self.printNonPassesSummary(log)
		
	def printNonPassesSummary(self, log):
		showOutcomeReason = str(self.showOutcomeReason).lower() == 'true'
		showOutputDir = str(self.showOutputDir).lower() == 'true'
		showNonPassingTestIds = str(self.showTestIdList).lower() == 'true'

		log.critical("Summary of non passes: ")
		fails = 0
		for cycle in list(self.results.keys()):
			for outcome in list(self.results[cycle].keys()):
				if outcome in FAILS : fails = fails + len(self.results[cycle][outcome])
		if fails == 0:
			log.critical("	THERE WERE NO NON PASSES", extra=ColorLogFormatter.tag(LOG_PASSES))
		else:
			failedids = set()
			for cycle in list(self.results.keys()):
				cyclestr = ''
				if len(self.results) > 1: cyclestr = '[CYCLE %d] '%(cycle+1)
				for outcome in FAILS:
					for (id, reason, outputdir) in self.results[cycle][outcome]: 
						failedids.add(id)
						log.critical("  %s%s: %s ", cyclestr, LOOKUP[outcome], id, extra=ColorLogFormatter.tag(LOOKUP[outcome].lower()))
						if showOutputDir:
							log.critical("      %s", os.path.normpath(os.path.relpath(outputdir)))
						if showOutcomeReason and reason:
							log.critical("      %s", reason, extra=ColorLogFormatter.tag(LOG_TEST_OUTCOMES))
		
			if showNonPassingTestIds and len(failedids) > 1:
				# display just the ids, in a way that's easy to copy and paste into a command line
				failedids = list(failedids)
				failedids.sort()
				if len(failedids) > 20: # this feature is only useful for small test runs
					failedids = failedids[:20]+['...']
				log.critical('')
				log.critical('List of non passing test ids:')
				log.critical('%s', ' '.join(failedids))

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
