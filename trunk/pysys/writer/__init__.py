#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net

"""
Contains implementations of test output summary writers used to output test results during runtime execution. 

There are currently four implementations of writers distributed with the PySys framework,
namely the L{writer.TextResultsWriter}, the L{writer.XMLResultsWriter}, the
L{writer.JUnitXMLResultsWriter} and the L{writer.CSVResultsWriter}. Project configuration of
the writers is through the PySys project file using the <writer> tag - multiple writers may
be configured and their individual properties set through the nested <property> tag. Writer
properties are set as attributes to the class through the setattr() function. Custom (site
specific) modules can be created and configured by users of the PySys framework (e.g. to
output test results into a relational database etc), though they must adhere to the interface
demonstrated by the implementations demonstrated here.

The writers are instantiated and invoked by the L{pysys.baserunner.BaseRunner} class
instance. This calls the class constructors of all configured test writers, and then 
the setup (prior to executing the set of tests), processResult (process a test result), 
and cleanup (upon completion of the execution of all tests). The **kwargs method parameter
is used for variable argument passing in the interface methods to allow modification of 
the PySys framework without breaking writer implementations already in existence. Currently 
the L{pysys.baserunner.BaseRunner} includes numTests in the call to the setup action (the 
number of tests to be executed), and cycle in the call to the processResult action 
(the cycle number when iterations through the same set of tests was requested).

"""

__all__ = ["TextResultsWriter", "XMLResultsWriter", "CSVResultsWriter", "JUnitXMLResultsWriter"]

import logging, time, urlparse, os, stat

from pysys import log
from pysys.constants import *
from pysys.exceptions import *

from xml.dom.minidom import getDOMImplementation

class flushfile(): 
	"""Class to flush on each write operation.  
	
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


class TextResultsWriter:
	"""Class to log results to logfile in text format.
	
	Writing of the test summary file defaults to the working directory. This can be be over-ridden in the PySys 
	project file using the nested <property> tag on the <writer> tag.
	 
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The filename template for the logging of test results
		
		"""	
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

		try:
			self.fp = flushfile(open(self.logfile, "w"))
			self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
			self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
			self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))
		except:
			pass


	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 
		
		Flushes and closes the file handle to the logfile.  

		@param kwargs: Variable argument list
				
		"""
		try:
			if self.fp: 
				self.fp.write('\n\n\n')
				self.fp.close()
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

			
	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Writes the test id and outcome to the logfile. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""
		if kwargs.has_key("cycle"): 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.fp.write('\n[Cycle %d]:\n'%self.cycle)	
		
		self.fp.write("%s: %s\n" % (LOOKUP[testObj.getOutcome()], testObj.descriptor.id))

		
		
class XMLResultsWriter:
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

	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The filename template for the logging of test results
		
		"""
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.cycle = -1
		self.numResults = 0
		self.fp = None


	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the DOM for the test output summary and writes to logfile. 
						
		@param kwargs: Variable argument list
		
		"""
		self.numTests = kwargs["numTests"] if kwargs.has_key("numTests") else 0 
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile
		
		try:
			self.fp = flushfile(open(self.logfile, "w"))
		
			impl = getDOMImplementation()
			self.document = impl.createDocument(None, "pysyslog", None)
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
			element.appendChild(self.document.createTextNode(self.__pathToURL(PROJECT.root)))
			self.rootElement.appendChild(element)

			# add the extra params nodes
			element = self.document.createElement("xargs")
			if kwargs.has_key("xargs"): 
				for key in kwargs["xargs"].keys():
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
			self.fp.write(self.document.toprettyxml(indent="  "))
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)


	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 
		
		Updates the test run status in the DOM, and re-writes to logfile.

		@param kwargs: Variable argument list
				
		"""
		self.fp.seek(0)
		self.statusAttribute.value="complete"
		self.fp.write(self.document.toprettyxml(indent="  "))
		try:
			if self.fp: self.fp.close()
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

			
	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Adds the results node to the DOM and re-writes to logfile.
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
		self.fp.seek(0)
		
		if kwargs.has_key("cycle"): 
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
				
		# write the file out
		self.fp.write(self.document.toprettyxml(indent="  "))
    	

	def __createResultsNode(self):
		self.resultsElement = self.document.createElement("results")
		cycleAttribute = self.document.createAttribute("cycle")
		cycleAttribute.value="%d"%self.cycle
		self.resultsElement.setAttributeNode(cycleAttribute)
		self.rootElement.appendChild(self.resultsElement)

    	
	def __pathToURL(self, path):
		try: 
			if self.useFileURL.lower() == "false": return path
		except:
			return path
		else:
			return urlparse.urlunparse(["file", HOSTNAME, path.replace("\\", "/"), "","",""])
	
	
class JUnitXMLResultsWriter:
	"""Class to log test results in Apache Ant JUnit XML format (one output file per test per cycle). 
	
	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string
	
	"""
	outputDir = None
	
	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.
		
		@param logfile: The (optional) filename template for the logging of test results
		
		"""	
		self.cycle = -1


	def setup(self, **kwargs):	
		"""Implementation of the setup method.

		Creates the output directory for the writing of the test summary files.  
						
		@param kwargs: Variable argument list
		
		"""	
		self.outputDir = os.path.join(PROJECT.root, 'target','pysys-reports') if self.outputDir is None else self.outputDir
		if os.path.exists(self.outputDir): self.purgeDirectory(self.outputDir, True)
		os.makedirs(self.outputDir)

		
	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method. 

		@param kwargs: Variable argument list
				
		"""
		pass
			

	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method. 
		
		Creates a test summary file in the Apache Ant Junit XML format. 
		
		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list
		
		"""	
		if kwargs.has_key("cycle"): 
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
		rootElement.setAttributeNode(attr1)
		rootElement.setAttributeNode(attr2)
		rootElement.setAttributeNode(attr3)
		rootElement.setAttributeNode(attr4)
		
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
			fp = open(os.path.join(testObj.output, 'run.log'))
			stdout.appendChild(document.createTextNode(fp.read()))
			fp.close()
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		if self.cycle > 0:
			fp = open(os.path.join(self.outputDir,'TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle)), 'w')
		else:
			fp = open(os.path.join(self.outputDir,'TEST-%s.xml'%(testObj.descriptor.id)), 'w')
		fp.write(document.toprettyxml(indent='	'))
		fp.close()
		

	def purgeDirectory(self, dir, delTop=False):
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


class CSVResultsWriter:
	"""Class to log results to logfile in CSV format.

	Writing of the test summary file defaults to the working directory. This can be be over-ridden in the PySys
	project file using the nested <property> tag on the <writer> tag. The CSV column output is in the form;

	id, title, cycle, startTime, duration, outcome

	@ivar outputDir: Path to output directory to write the test summary files
	@type outputDir: string

	"""
	outputDir = None

	def __init__(self, logfile):
		"""Create an instance of the TextResultsWriter class.

		@param logfile: The filename template for the logging of test results

		"""
		self.logfile = time.strftime(logfile, time.gmtime(time.time()))
		self.fp = None


	def setup(self, **kwargs):
		"""Implementation of the setup method.

		Creates the file handle to the logfile and logs initial details of the date,
		platform and test host.

		@param kwargs: Variable argument list

		"""
		self.logfile = os.path.join(self.outputDir, self.logfile) if self.outputDir is not None else self.logfile

		try:
			self.fp = flushfile(open(self.logfile, "w"))
			self.fp.write('id, title, cycle, startTime, duration, outcome\n')
		except:
			pass


	def cleanup(self, **kwargs):
		"""Implementation of the cleanup method.

		Flushes and closes the file handle to the logfile.

		@param kwargs: Variable argument list

		"""
		try:
			if self.fp:
				self.fp.write('\n\n\n')
				self.fp.close()
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)


	def processResult(self, testObj, **kwargs):
		"""Implementation of the processResult method.

		Writes the test id and outcome to the logfile.

		@param testObj: Reference to an instance of a L{pysys.basetest.BaseTest} class
		@param kwargs: Variable argument list

		"""
		testStart = kwargs["testStart"] if kwargs.has_key("testStart") else time.time()
		testTime = kwargs["testTime"] if kwargs.has_key("testTime") else 0
		cycle = kwargs["cycle"] if kwargs.has_key("cycle") else 0

		csv = []
		csv.append(testObj.descriptor.id)
		csv.append('\"%s\"'%testObj.descriptor.title)
		csv.append(str(cycle))
		csv.append((time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(testStart))))
		csv.append(str(testTime))
		csv.append(LOOKUP[testObj.getOutcome()])
		self.fp.write('%s \n' % ','.join(csv))
