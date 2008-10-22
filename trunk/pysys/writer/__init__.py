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

__all__ = []

import logging, time
from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *

from xml.dom.minidom import getDOMImplementation

log = logging.getLogger('pysys.writer')
log.setLevel(logging.NOTSET)


class LogFileResultsWriter:
	"""Class to log results to a logfile in the current directory."""
	
	def __init__(self, logfile):
		self.logfile = logfile
		self.cycle = -1
		self.fp = None


	def setup(self):
		try:
			self.fp = open(self.logfile, "w", 0)
			self.fp.write('DATE:       %s (GMT)\n' % (time.strftime('%y-%m-%d %H:%M:%S', time.gmtime(time.time())) ))
			self.fp.write('PLATFORM:   %s\n' % (PLATFORM))
			self.fp.write('TEST HOST:  %s\n' % (HOSTNAME))
		except:
			pass


	def cleanup(self):
		try:
			if self.fp: 
				self.fp.write('\n\n\n')
				self.fp.flush()
				self.fp.close()
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

			
	def writeResult(self, testObj, **kwargs):
		if kwargs.has_key("cycle"): 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.fp.write('\n[Cycle %d]:\n'%self.cycle)	
		
		self.fp.write("%s: %s\n" % (LOOKUP[testObj.getOutcome()], testObj.descriptor.id))

		
		
class XMLFileResultsWriter:

	def __init__(self, logfile):
		self.logfile = logfile
		self.cycle = -1
		self.fp = None


	def get_site_packages_path(self):
		if sys.platform.lower().startswith('win'):
			return os.path.join(sys.prefix, "Lib", "site-packages")
		else:
			return os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")


	def setup(self):
		try:
			self.fp = open(self.logfile, "w", 0)
		
			impl = getDOMImplementation()
			self.document = impl.createDocument(None, "pysyslog", None)
			stylesheet = self.document.createProcessingInstruction("xml-stylesheet", "href=\"%s\" type=\"text/xsl\"" % (os.path.join(self.get_site_packages_path(), 'pysys-log.xsl')))
			self.document.insertBefore(stylesheet, self.document.childNodes[0])
		
			self.rootElement = self.document.documentElement
			self.statusAttribute = self.document.createAttribute("status")
			self.statusAttribute.value="running"
			self.rootElement.setAttributeNode(self.statusAttribute)

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
			element.appendChild(self.document.createTextNode(PROJECT.root))
			self.rootElement.appendChild(element)

			# write the file out
			self.fp.write(self.document.toprettyxml(indent="  "))
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)


	def createResultsNode(self):
		# create the results entry
		self.resultsElement = self.document.createElement("results")
		cycleAttribute = self.document.createAttribute("cycle")
		cycleAttribute.value="%d"%self.cycle
		self.resultsElement.setAttributeNode(cycleAttribute)
		self.rootElement.appendChild(self.resultsElement)


	def cleanup(self):
		self.fp.seek(0)
		self.statusAttribute.value="complete"
		self.fp.write(self.document.toprettyxml(indent="  "))
		try:
			if self.fp: 
				self.fp.flush()
				self.fp.close()
		except:
			log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)

			
	def writeResult(self, testObj, **kwargs):
		self.fp.seek(0)
		
		if kwargs.has_key("cycle"): 
			if self.cycle != kwargs["cycle"]:
				self.cycle = kwargs["cycle"]
				self.createResultsNode()
		
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
		element.appendChild(self.document.createTextNode(testObj.descriptor.file))
		resultElement.appendChild(element)

		element = self.document.createElement("output")
		element.appendChild(self.document.createTextNode(testObj.output))
		resultElement.appendChild(element)
		
		self.resultsElement.appendChild(resultElement)
	
		# write the file out
		self.fp.write(self.document.toprettyxml(indent="  "))
    	
