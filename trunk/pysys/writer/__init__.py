#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2012  M.B.Grieve

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
Contains implementations of test output summary writers used to output test results during runtime execution, 

There are currently three implementations of writers distributed with the PySys framework, 
namely the L{writer.TextResultsWriter}, the L{writer.XMLResultsWriter} and the 
L{writer.JUnitXMLResultsWriter). Project configuration of the writers is through the PySys 
project file using the <writer> tag - multiple writers may be configured and their individual 
properties set through the nested <property> tag. Writer properties are set as attributes to 
the class through the setattr() function. Custom (site specific) modules can be created and 
configured by users of the PySys framework (e.g. to output test results into a relational 
database etc), though they must adhere to the interface demonstrated by the implementations 
demonstrated here. 

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

__all__ = ["TextResultsWriter", "XMLResultsWriter"]

import logging, time, urlparse

from pysys import log
from pysys.constants import *
from pysys.exceptions import *

from xml.dom.minidom import getDOMImplementation

class flushfile(file): 
	"""Class to flush on each write operation.  
	
	"""
	fp=None 
	
	def __init__(self, fp): 
		"""Create an instance of the class. 
		
		@param fp: The file object
		"""
		self.fp = file
	
	def write(self, msg) 
		"""Perform a write to the file object.
		
		@param msg: The string message to write. 
		"""
		if self.fp != None:
			self.fp.write(msg) 
			self.fp.flush() 
		
	def close(self)
		"""Close the file objet."""
		if self.fp != None: self.fp.close()


class TextResultsWriter:
	"""Class to log results to logfile in text format.
	
	"""
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
		try:
			self.fp = flushfile(open(self.logfile, "w")
			self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
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
	logfile using toprettyxml(). The stylesheet and useFileURL attributes of the class can be over-ridden in the PySys
	project file using the nested <property> tag on the <writer> tag.
	 
	@ivar stylesheet: Path to the XSL stylesheet
	@type stylesheet: string
	@ivar useFileURL: Indicates if full file URLs are to be used for local resource references 
	@type useFileURL: string (true | false)
	
	"""
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
		numTests = 0
		if kwargs.has_key("numTests"): 
			self.numTests = kwargs["numTests"]

		try:
			self.fp = flushfile(open(self.logfile, "w", 0))
		
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
			element.appendChild(self.document.createTextNode(time.strftime('%y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
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
		
		element = self.document.createElement("timestamp")
		element.appendChild(self.document.createTextNode(time.strftime('%y-%m-%d %H:%M:%S', time.gmtime(time.time()))))
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
	def __init__(self, logfile):
		self.cycle = -1
		self.reports = os.path.join(PROJECT.root, 'target','pysys-reports')

	def setup(self, **kwargs):		
		if os.path.exists(self.reports): self.purgeDirectory(self.reports, True)
		os.makedirs(self.reports)

	def cleanup(self, **kwargs):
		pass
			
	def processResult(self, testObj, **kwargs):
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
						
			stdout = document.createElement('system-out')
			fp = open(os.path.join(testObj.output, 'run.log'))
			stdout.appendChild(document.createTextNode(fp.read()))
			fp.close()
			
			testcase.appendChild(failure)
			testcase.appendChild(stdout)
		rootElement.appendChild(testcase)
		
		# write out the test result
		if self.cycle > 0:
			fp = open(os.path.join(self.reports,'TEST-%s.%s.xml'%(testObj.descriptor.id, self.cycle)), 'w')
		else:
			fp = open(os.path.join(self.reports,'TEST-%s.xml'%(testObj.descriptor.id)), 'w')
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

		if delTop: os.rmdir(dir)
		