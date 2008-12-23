#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

"""
Contains implementations of test output summary writers used to output test results during runtime execution, 

There are currently two implementations of writers distributed with the PySys framework, 
namely the TextResultsWriter and the XMLResultsWriter. Project configuration of the writers 
is through the PySys project file using the <writer> tag - multiple writers may 
be configured and their individual properties set through the nested <property>
tag. Writer properties are set as attributes to the class through the setattr() 
function. Custom (site specific) modules can be created and configured by users of 
the PySys framework (e.g. to output test results into a relational database etc), 
though they must adhere to the interface demonstrated by the implementations 
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
			self.fp = open(self.logfile, "w", 0)
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
				self.fp.flush()
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
			self.fp = open(self.logfile, "w", 0)
		
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
			if self.fp: 
				self.fp.flush()
				self.fp.close()
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
	