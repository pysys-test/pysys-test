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
Writers that record test outcomes to a variety of file formats. 

"""

__all__ = [
	"TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter",
	]

import time, stat, logging, sys, io
import zipfile
import locale
import shutil
import shlex
if sys.version_info[0] == 2:
	from urlparse import urlunparse
else:
	from urllib.parse import urlunparse

from pysys.constants import *
from pysys.writer.api import *
from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes, stdoutPrint
from pysys.utils.fileutils import mkdir, deletedir, toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2, openfile
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
		self.logfile = time.strftime(logfile, time.localtime(time.time()))
		self.cycle = -1
		self.fp = None

	def setup(self, **kwargs):
		# Creates the file handle to the logfile and logs initial details of the date, 
		# platform and test host. 

		self.logfile = os.path.normpath(os.path.join(self.outputDir or kwargs['runner'].output+'/..', self.logfile))

		self.fp = flushfile(openfile(self.logfile, "w", encoding=None if PY2 else 'utf-8'))
		self.fp.write('DATE:       %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S (%Z)', time.localtime(time.time())) ))
		self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
		self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))
		self.fp.write('\n')
		for k, v in kwargs['runner'].runDetails.items():
			if k in {'startTime', 'hostname'}: continue # don't duplicate the above
			self.fp.write("%-20s%s\n"%(k+': ', v))

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
		
		self.fp.write("%s: %s\n" % (testObj.getOutcome(), testObj.descriptor.id))

class XMLResultsWriter(BaseRecordResultsWriter):
	"""Class to log results to logfile in a single XML file.
	
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
		
		try:
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
	"""Class to log test results in the widely-used Apache Ant JUnit XML format (one output file per test per cycle). 
	
	If you need to integrate with any CI provider that doesn't have built-in support (e.g. Jenkins) this standard 
	output format will usually be the easiest way to do it. 
	
	The output directory is published as with category name "JUnitXMLResultsDir". 
	
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
		self.outputDir = os.path.normpath((os.path.join(kwargs['runner'].project.root, 'target','pysys-reports') if not self.outputDir else 
			os.path.join(kwargs['runner'].output+'/..', self.outputDir)))
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
		attr3.value = '%d'%(int)(testObj.getOutcome().isFailure())	
		attr4 = document.createAttribute('skipped')	
		attr4.value = '%d'%(int)(testObj.getOutcome() == SKIPPED)		
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
		attr1 = document.createAttribute('classname')
		attr1.value = testObj.descriptor.classname
		attr2 = document.createAttribute('name')
		attr2.value = testObj.descriptor.id		   	
		testcase.setAttributeNode(attr1)
		testcase.setAttributeNode(attr2)
		
		# add in failure information if the test has failed
		if (testObj.getOutcome().isFailure()):
			failure = document.createElement('failure')
			attr = document.createAttribute('message')
			attr.value = '%s%s'%(testObj.getOutcome(), (': %s'%testObj.getOutcomeReason()) if testObj.getOutcomeReason() else '')
			failure.setAttributeNode(attr)

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
	"""Class to log results to logfile in CSV format.

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

		self.fp = flushfile(openfile(self.logfile, "w", encoding=None if PY2 else 'utf-8'))
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

