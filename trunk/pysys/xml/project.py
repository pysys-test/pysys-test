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

import os, os.path, sys, string, logging, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.xml.project')

DTD='''
<!ELEMENT pysysproject (property+, path+, runner?) >
<!ATTLIST property environment CDATA #IMPLIED
                   osfamily CDATA #IMPLIED
                   file CDATA #IMPLIED
                   name CDATA #IMPLIED
                   value CDATA #IMPLIED
                   default CDATA #IMPLIED>
<!ATTLIST runner classname CDATA #REQUIRED
                 module CDATA #REQUIRED>
<!ATTLIST path value CDATA #REQUIRED
               relative CDATA #IMPLIED>

'''

PROPERTY_EXPAND_ENV = "(?P<replace>\${%s.(?P<key>.*?)})"
PROPERTY_EXPAND = "(?P<replace>\${(?P<key>.*?)})"
PROPERTY_FILE = "(?P<name>^.*)=(?P<value>.*)$"


class XMLProjectParser:
	def __init__(self, xmlfile):
		self.dirname = os.path.dirname(xmlfile)
		self.xmlfile = xmlfile
		self.environment = 'env'
		self.osfamily = 'osfamily'
		self.properties = {self.osfamily:OSFAMILY}
		
		if not os.path.exists(xmlfile):
			raise Exception, "Unable to find supplied project file \"%s\"" % xmlfile
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except:
			raise Exception, "Error parsing supplied project file, " % (sys.exc_info()[1])
		else:
			if self.doc.getElementsByTagName('pysysproject') == []:
				raise Exception, "No <pysysproject> element supplied in project file"
			else:
			
				self.root = self.doc.getElementsByTagName('pysysproject')[0]

				
	def unlink(self):
		if self.doc: self.doc.unlink()	


	def getProperties(self):
		propertyNodeList = self.root.getElementsByTagName('property')

		for propertyNode in propertyNodeList:
			if propertyNode.hasAttribute("environment"):
				self.environment = propertyNode.getAttribute("environment")
			
			elif propertyNode.hasAttribute("osfamily"):
				self.properties.pop(self.osfamily, "")
				self.osfamily = propertyNode.getAttribute("osfamily")
				self.properties[self.osfamily] = OSFAMILY
				 	
			elif propertyNode.hasAttribute("file"): 
				file = self.expandFromProperty(propertyNode.getAttribute("file"), propertyNode.getAttribute("default"))
				self.getPropertiesFromFile(os.path.join(self.dirname, file))
			
			elif propertyNode.hasAttribute("name"):
				name = propertyNode.getAttribute("name") 
				value = self.expandFromEnvironent(propertyNode.getAttribute("value"), propertyNode.getAttribute("default"))
				self.properties[name] = self.expandFromProperty(value, propertyNode.getAttribute("default"))
	
		return self.properties


	def getPropertiesFromFile(self, file):
		if os.path.exists(file):
			try:
				fp = open(file, "r")
			except:	
				pass
			else:
				for line in fp.readlines():
					regex = re.compile(PROPERTY_FILE, re.M)
					if regex.search(line) != None:
						name = re.match(regex, line).group('name')
			 			value = re.match(regex, line).group('value')			 		
						value = self.expandFromProperty(value, "")				
						self.properties[name.strip()] = value.strip()


	def expandFromEnvironent(self, value, default):
		regex = re.compile(PROPERTY_EXPAND_ENV%self.environment, re.M)
		while regex.search(value) != None:
			matches = regex.findall(value)				
			for m in matches:
				try:
					insert = os.environ[m[1]]
				except :
					insert = default
				value = string.replace(value, m[0], insert)
		return value		


	def expandFromProperty(self, value, default):
		regex = re.compile(PROPERTY_EXPAND, re.M)
		while regex.search(value) != None:
			matches = regex.findall(value)
			for m in matches:
				try:
					insert = self.properties[m[1]]
				except :
					insert = default
				value = string.replace(value, m[0], insert)
		return value


	def getRunnerDetails(self):
		try:
			runnerNodeList = self.root.getElementsByTagName('runner')[0]
			return [runnerNodeList.getAttribute('classname'), runnerNodeList.getAttribute('module')]
		except:
			return [DEFAULT_RUNNER_CLASS, DEFAULT_RUNNER_MODULE]


	def addToPath(self):		
		pathNodeList = self.root.getElementsByTagName('path')

		for pathNode in pathNodeList:
			try:
				value = pathNode.getAttribute("value") 
				relative = pathNode.getAttribute("relative")
		
				if relative == "true": value = os.path.join(self.dirname, value)
				sys.path.append(os.path.normpath(value))

			except:
				pass


	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()
		
