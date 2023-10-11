#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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
Writers that record test outcomes to a variety of file formats. 

"""

__all__ = [
	"TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter","JSONResultsWriter",
	]

import time, stat, logging, sys, io
import zipfile
import locale
import shutil
import shlex
from urllib.parse import urlunparse
import json

from pysys.constants import *
from pysys.writer.api import *
from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes, stdoutPrint
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import openfile
from pysys.exceptions import UserError

from xml.dom.minidom import getDOMImplementation

log = logging.getLogger('pysys.writer')

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

class JSONResultsWriter(BaseRecordResultsWriter, ArtifactPublisher):
	"""Writer to log a summary of the test results to a single JSON file, along with ``runDetails`` from the runner, 
	and a list of published ``artifacts`` (e.g. code coverage etc).
	
	The following fields are always included for each test result:
	
	  - testId: the test id, including ``~mode`` suffix if it has modes defined.
	  - outcome: the outcome string e.g. "NOT VERIFIED". 
	  - outcomeReason: the string explaining the reason for the outcome, or empty if not available. 
	  - startTime: the time the test started, in ``%Y-%m-%d %H:%M:%S`` format and in the local timezone.
	  - durationSecs: how long the test executed for (or ``None``/``null`` if unknown). 
	  - testDir: the path to this test under the ``testRootDir``, using forward slashes. 
	  - testFile: the path (typically relative to testDir, using forward slashes) of the main file containing the 
	    test's logic, e.g. ``pysystest.py``, ``run.py`` etc. This is usually, but not always, a Python file. 

	If applicable, some tests/runs may have additional fields such as ``cycle``, ``title`` and ``outputDir``. 

	.. versionadded:: 2.1

	.. versionchanged:: 2.2 Added ``artifacts`` dictionary recording artifact paths published during execution of the tests, for 
	    example code coverage and performance reports. 
	
	"""
	
	includeTitle = True
	"""
	By default the title of each test is included in the output. 
	
	To save disk space you can set this to False if it is not needed. 
	"""
	
	includeNonFailureOutcomes = '*'
	"""
	In addition to failure outcomes, any outcomes listed here (as comma-separated display names, e.g. 
	``"NOT VERIFIED, INSPECT"``) will be included. To include all non-failure outcomes, set this to the special value ``"*"``. 
	
	To save disk space and record only failure outcomes, you may set this to an empty string. 
	"""

	outputDir = None
	"""
	The directory to write the logfile, if an absolute path is not specified. The default is the working directory. 

	Project ``${...}`` properties can be used in the path. 
	"""
	
	def __init__(self, logfile, **kwargs):
		super().__init__(logfile, **kwargs)
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.localtime(time.time()))
		self.fp = None
		self.artifacts = {} # category: [paths]

	def setup(self, **kwargs):
		self.runner = kwargs['runner']
		# NB: this method is also called by ConsoleFailureAnnotationsWriter
		self.includeNonFailureOutcomes = [str(o) for o in OUTCOMES] if self.includeNonFailureOutcomes=='*' else [o.strip().upper() for o in self.includeNonFailureOutcomes.split(',') if o.strip()]
		for o in self.includeNonFailureOutcomes:
			if not any(o == str(outcome) for outcome in OUTCOMES):
				raise UserError('Unknown outcome display name "%s" in includeNonFailureOutcomes'%o)


		self.logfile = os.path.normpath(os.path.join(self.outputDir or kwargs['runner'].output+'/..', self.logfile))
		mkdir(os.path.dirname(self.logfile))

		self.resultsWritten = 0
		self.cycles = self.runner.cycles

		if self.fp is None: # this condition allows a subclass to write to something other than a .json file
			self.fp = io.open(self.logfile, "w", encoding='utf-8')
		self.fp.write('{"runDetails": ')
		json.dump(self.runner.runDetails, self.fp)
		self.fp.write(', "results":[\n')
		self.fp.flush()

	def publishArtifact(self, path, category, **kwargs):
		# to keep the file readable, store artifacts and put them all at the end
		self.artifacts.setdefault(category, []).append(path)

	def cleanup(self, **kwargs):
		if not self.fp: return

		self.fp.write('\n],')

		self.fp.write('"artifacts": ')
		json.dump(self.artifacts, self.fp)
		self.fp.write('}\n')
		
		self.fp.close()
		self.fp = None
		
		with io.open(self.logfile, encoding='utf-8') as fp:
			json.load(fp) # sanity check that valid JSON was generated by this JSONResultsWriter


	def createTestResultDict(self, testObj, **kwargs):
		"""
		Creates the dict that will be output for each test result.
		
		@returns: The dict, or ``None`` if this result should not be included/ 
		"""
		testDir = fromLongPathSafe(testObj.descriptor.testDir)
		if testDir.startswith(self.runner.project.testRootDir):
			testDir = testDir[len(self.runner.project.testRootDir)+1:]

		data = {
			'testId': testObj.descriptor.id, # includes mode suffix
			'outcome': str(testObj.getOutcome()),
			'outcomeReason': testObj.getOutcomeReason(),
			'startTime': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime( kwargs.get('testStart', time.time()) )),
			'durationSecs': kwargs.get("testTime", -1),
			'testDir': fromLongPathSafe(testDir).replace('\\', '/'),
			'testFile': fromLongPathSafe(testObj.descriptor._getTestFile()).replace('\\','/'),
		}
		if self.cycles > 1:
			data['cycle'] = kwargs["cycle"]+1
		if testObj.descriptor.output != 'Output': data['outputDir'] = fromLongPathSafe(testObj.descriptor.output).replace('\\', '/')
		
		if self.includeTitle: data['title'] = testObj.descriptor.title
		
		return data

	def processResult(self, testObj, **kwargs):
		
		outcome = testObj.getOutcome()
		if not (outcome.isFailure() or str(outcome) in self.includeNonFailureOutcomes): return

		data = self.createTestResultDict(testObj, **kwargs)
		if not data: return
		
		if self.resultsWritten > 0:
			self.fp.write(',\n')
		self.resultsWritten += 1
		
		json.dump(data, self.fp)
		self.fp.flush()


class TextResultsWriter(BaseRecordResultsWriter):
	"""Writer to log a summary of the results to a log file in text format.
	
	Only enabled when the record flag is specified.

	Can be a useful way to view the current or final status of the current/latest test run. 
	The file is written incrementally as each test completes, but can be sorted (using standard command line tools) 
	to get a nice summary of all the failures. 
	"""

	outputDir = None
	"""
	The directory to write the logfile, if an absolute path is not specified. The default is the working directory. 

	Project ``${...}`` properties can be used in the path, for example ``${eval:os.path.expanduser('~')}`` for the current user's home directory. 
	"""

	verbose = False
	"""
	Display more details in the output including the outcome reason and the test title. 

	.. versionadded:: 2.2
	"""
	
	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.localtime(time.time()))
		self.cycle = -1
		self.fp = None

	def setup(self, **kwargs):
		# Creates the file handle to the logfile and logs initial details of the date, 
		# platform and test host. 

		self.logfile = os.path.normpath(os.path.join(self.outputDir or kwargs['runner'].output+'/..', self.logfile))
		log.info('TextResultsWriter is recording results at: %s', self.logfile)

		self.fp = flushfile(openfile(self.logfile, "w", encoding='utf-8', errors='backslashreplace'))
		if not self.verbose: # these are a bit ugly; keep them for compat, but for people using the new verbose mode don't bother
			self.fp.write('DATE:       %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S (%Z)', time.localtime(time.time())) ))
			self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
			self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))
		for k, v in kwargs['runner'].runDetails.items():
			if (not self.verbose) and k in {'startTime', 'hostname'}: continue # don't duplicate the above
			self.fp.write("%-20s%s\n"%(k+': ', v))
		self.fp.write('\n')

		self.failureIds = set()
		self.executed = 0

	def cleanup(self, **kwargs):
		# Flushes and closes the file handle to the logfile.  

		if self.fp: 
			self.fp.write('\n')
			if self.verbose:
				self.fp.write('Completed execution of %d tests%s\n'%(self.executed, f', and found {len(self.failureIds)} failures:' if self.failureIds else ''))
				if self.failureIds:
					self.fp.write(' '.join(sorted(list(self.failureIds))))

			self.fp.close()
			self.fp = None

	def processResult(self, testObj, cycle=None, **kwargs):
		# Writes the test id and outcome to the logfile. 
		
		if (not self.verbose) and cycle is not None and self.runner.threads==1 and self.runner.cycles>1:  # only makes sense to group by cycles if single-threaded
			if self.cycle != cycle:
				self.cycle = cycle
				self.fp.write('\n[Cycle %d]:\n'%(self.cycle+1))


		if self.verbose:
			self.executed += 1
			if testObj.getOutcome().isFailure():
				self.failureIds.add(testObj.descriptor.id)
			# This is designed to permit sorting the entire file such that similar "reasons" grouped together
			# Providing the absolute path of the output dir allows jumping to the relevant files in an editor
			text = '* '+str(testObj)

			if testObj.descriptor.title and testObj.descriptor.title != testObj.descriptor.idWithoutMode: text += f" | {testObj.descriptor.title}"
			# use ! vs + to ensure failures are all sorted together
			text += f"\n  {'! ' if testObj.getOutcome().isFailure() else '+ '}{testObj.getOutcome()}{' '+testObj.getOutcomeReason() if testObj.getOutcomeReason() else ''} - {testObj.output}"
		else:
			text = "%s: %s" % (testObj.getOutcome(), 
				# Use str() which includes cycle if a) we need to and b) we haven't already displayed it above
				str(testObj) if self.runner.cycles>1 and self.runner.threads>1
				else testObj.descriptor.id)

		self.fp.write(text+'\n')


class XMLResultsWriter(BaseRecordResultsWriter):
	"""Writer to log results to logfile in a single XML file.
	
	The class creates a DOM document to represent the test output results and writes the DOM to the 
	logfile using toprettyxml(). The outputDir, stylesheet, useFileURL attributes of the class can 
	be overridden in the PySys project file using the nested <property> tag on the <writer> tag.
	 
	:ivar str ~.outputDir: Path to output directory to write the test summary files
	:ivar str ~.stylesheet: Path to the XSL stylesheet
	:ivar str ~.useFileURL: Indicates if full file URLs are to be used for local resource references 
	
	"""
	outputDir = None
	stylesheet = DEFAULT_STYLESHEET
	useFileURL = "false"

	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.localtime(time.time()))
		self.cycle = -1
		self.numResults = 0
		self.fp = None

	def setup(self, **kwargs):
		# Creates the DOM for the test output summary and writes to logfile. 
						
		self.numTests = kwargs["numTests"] if "numTests" in kwargs else 0 
		self.logfile = os.path.normpath(os.path.join(self.outputDir or kwargs['runner'].output+'/..', self.logfile))
		
		mkdir(os.path.dirname(self.logfile))
		self.fp = io.open(toLongPathSafe(self.logfile), "wb")
	
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
		element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
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
		outcomeAttribute.value=str(testObj.getOutcome())
		resultElement.setAttributeNode(nameAttribute)
		resultElement.setAttributeNode(outcomeAttribute)

		element = self.document.createElement("outcomeReason")
		element.appendChild(self.document.createTextNode( testObj.getOutcomeReason() ))
		resultElement.appendChild(element)
		
		element = self.document.createElement("timestamp")
		element.appendChild(self.document.createTextNode(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
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
	"""Writer to log test results in the widely-used Apache Ant JUnit XML format (one output file per test per cycle). 
	
	If you need to integrate with any CI provider that doesn't have built-in support (e.g. Jenkins) this standard 
	output format will usually be the easiest way to do it. 
	
	The output directory is published as with category name "JUnitXMLResultsDir". 
	
	"""
	outputDir = None
	"""
	The directory to write the XML files to, as an absolute path, or relative to the testRootDir. 

	Project ``${...}`` properties can be used in the path. 
	"""

	testsuiteName = None
	"""
	Overrides the content written to the ``<testsuite name=...>`` attribute (defaults to ``@TESTID@``), 
	A recommended alternate value is ``@TESTID_PACKAGE@`` which represents the test id up to the final ``.``. 

	.. versionadded:: 2.2
	"""
	testcaseClassname = None
	"""
	Overrides the content written to the ``<testcase classname=...>`` attribute (defaults to ``@CLASSNAME@``), 
	A recommended alternate value is empty string, since the classname (typically "PySys") is not very useful for most PySys tests. 

	.. versionadded:: 2.2
	"""
	testcaseName = None # default is @TESTID@
	"""
	Overrides the content written to the ``<testcase name=...>`` attribute (defaults to ``@TESTID@``), 
	A recommended alternate value is ``@TESTID_NO_PACKAGE_OR_MODE@~@MODE@`` when using ``testsuiteName`` to hold the package part of the test id. 

	.. versionadded:: 2.2
	"""

	def __init__(self, **kwargs):
		self.cycle = -1

	def setup(self, **kwargs):	
		# Creates the output directory for the writing of the test summary files.  
		self.outputDir = os.path.normpath((os.path.join(kwargs['runner'].project.root, 'target','pysys-reports') if not self.outputDir else 
			os.path.join(kwargs['runner'].output+'/..', self.outputDir)))
		deletedir(self.outputDir)
		mkdir(self.outputDir)
		self.cycles = kwargs.pop('cycles', 0)

	def substitute(self, configured, default, descriptor):
		if configured is None: return default # but not if it's empty!
		if '@' not in configured: return configured

		id = descriptor.idWithoutMode.split('.')
		TESTID_PACKAGE = '.'.join(id[:-1])
		TESTID_NO_PACKAGE_OR_MODE = id[-1]

		return (configured
			.replace('@TESTID_NO_PACKAGE_OR_MODE@', TESTID_NO_PACKAGE_OR_MODE)
			.replace('@TESTID_PACKAGE@', TESTID_PACKAGE)
			.replace('@TESTID@', descriptor.id)
			.replace('@MODE@', descriptor.mode or '')
			.replace('@CLASSNAME@', descriptor.classname)
		).lstrip('.').rstrip('~') # stripping leading . helps cover cases where there is sometimes no package
		

	def processResult(self, testObj, **kwargs):
		# Creates a test summary file in the Apache Ant JUnit XML format. 
		
		outcome = testObj.getOutcome()
		
		if "cycle" in kwargs: 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
		
		impl = getDOMImplementation()		
		document = impl.createDocument(None, 'testsuite', None)		
		rootElement = document.documentElement
		attr1 = document.createAttribute('name')
		attr1.value = self.substitute(self.testsuiteName, testObj.descriptor.id, testObj.descriptor)
		attr2 = document.createAttribute('tests')
		attr2.value='1'
		attr3 = document.createAttribute('failures')
		attr3.value = '%d'%int(outcome.isFailure())	
		attr4 = document.createAttribute('skipped')	
		attr4.value = '%d'%int(outcome == SKIPPED)		
		attr5 = document.createAttribute('time')	
		attr5.value = '%s'%kwargs['testTime']
		rootElement.setAttributeNode(attr1)
		rootElement.setAttributeNode(attr2)
		rootElement.setAttributeNode(attr3)
		rootElement.setAttributeNode(attr4)
		rootElement.setAttributeNode(attr5)
		attr = document.createAttribute('timestamp')	
		attr.value = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()) # use UTC/GMT like Ant does
		rootElement.setAttributeNode(attr)

		# add the testcase information
		testcase = document.createElement('testcase')
		if self.testcaseClassname != '@OMIT@': # probably not needed since empty string seems to work better, but useful to have the option (crrently undocumented)
			attr1 = document.createAttribute('classname')
			attr1.value = self.substitute(self.testcaseClassname, testObj.descriptor.classname, testObj.descriptor)
			testcase.setAttributeNode(attr1)
		attr2 = document.createAttribute('name')
		attr2.value = self.substitute(self.testcaseName, testObj.descriptor.id, testObj.descriptor)
		testcase.setAttributeNode(attr2)
		attr5 = document.createAttribute('time')	
		attr5.value = '%s'%kwargs['testTime']
		testcase.setAttributeNode(attr5)

		# add in failure information if the test has failed
		if (outcome.isFailure() or outcome == SKIPPED):
			failure = document.createElement('skipped' if outcome==SKIPPED else 'failure')
			attr = document.createAttribute('message')
			attr.value = '%s%s'%(outcome, (': %s'%testObj.getOutcomeReason()) if testObj.getOutcomeReason() else '')
			failure.setAttributeNode(attr)

			if outcome != SKIPPED:
				attr = document.createAttribute('type') # would be an exception class in a JUnit test
				attr.value = str(testObj.getOutcome())
				failure.setAttributeNode(attr)

			stdout = document.createElement('system-out')
			runLogOutput = stripANSIEscapeCodes(kwargs.get('runLogOutput','')) # always unicode characters
			runLogOutput = runLogOutput.replace('\r','').replace('\n', os.linesep)
			stdout.appendChild(document.createTextNode(runLogOutput))
			
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

	def cleanup(self, **kwargs):
		self.runner.publishArtifact(self.outputDir, 'JUnitXMLResultsDir')



class CSVResultsWriter(BaseRecordResultsWriter):
	"""Writer to log results to logfile in CSV format.

	Writing of the test summary file defaults to the working directory. This can be be over-ridden in the PySys
	project file using the nested <property> tag on the <writer> tag. The CSV column output is in the form::

		id, title, cycle, startTime, duration, outcome

	"""
	outputDir = None

	def __init__(self, logfile, **kwargs):
		# substitute into the filename template
		self.logfile = time.strftime(logfile, time.localtime(time.time()))
		self.fp = None

	def setup(self, **kwargs):
		# Creates the file handle to the logfile and logs initial details of the date,
		# platform and test host.

		self.logfile = os.path.normpath(os.path.join(self.outputDir or kwargs['runner'].output+'/..', self.logfile))

		self.fp = flushfile(openfile(self.logfile, "w", encoding='utf-8'))
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
		csv.append((time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(testStart))))
		csv.append(str(testTime))
		csv.append(str(testObj.getOutcome()))
		self.fp.write('%s \n' % ','.join(csv))

