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

import os, os.path, sys, string, logging, time, xml.dom.minidom

from pysys.constants import *

log = logging.getLogger('pysys.xml.project')

DTD='''
<!DOCTYPE pysysproject [
<!ELEMENT pysysproject (property*, path*, runner?, maker?, writers?, formatters?) >
<!ELEMENT property (#PCDATA)>
<!ELEMENT path (#PCDATA)>
<!ELEMENT runner (#PCDATA)>
<!ELEMENT maker (#PCDATA)>
<!ELEMENT formatters (formatter+) >
<!ELEMENT formatter (#PCDATA) >
<!ELEMENT writers (writer+) >
<!ELEMENT writer (property*) >
<!ATTLIST property root CDATA #IMPLIED>
<!ATTLIST property environment CDATA #IMPLIED>
<!ATTLIST property osfamily CDATA #IMPLIED>
<!ATTLIST property file CDATA #IMPLIED>
<!ATTLIST property name CDATA #IMPLIED>
<!ATTLIST property value CDATA #IMPLIED>
<!ATTLIST property default CDATA #IMPLIED>
<!ATTLIST path value CDATA #REQUIRED>
<!ATTLIST path relative CDATA #IMPLIED>
<!ATTLIST runner classname CDATA #REQUIRED>
<!ATTLIST runner module CDATA #REQUIRED>
<!ATTLIST maker classname CDATA #REQUIRED>
<!ATTLIST maker module CDATA #REQUIRED>
<!ATTLIST formatter name CDATA #REQUIRED>
<!ATTLIST formatter messagefmt CDATA #REQUIRED>
<!ATTLIST formatter datefmt CDATA #REQUIRED>
<!ATTLIST writer classname CDATA #REQUIRED>
<!ATTLIST writer module CDATA #REQUIRED>
<!ATTLIST writer file CDATA #IMPLIED>
]>
'''

PROPERTY_EXPAND_ENV = "(?P<replace>\${%s.(?P<key>.*?)})"
PROPERTY_EXPAND = "(?P<replace>\${(?P<key>.*?)})"
PROPERTY_FILE = "(?P<name>^.*)=(?P<value>.*)$"


class XMLProjectParser:
	def __init__(self, dirname, file):
		self.dirname = dirname
		self.xmlfile = os.path.join(dirname, file)
		self.rootdir = 'root'
		self.environment = 'env'
		self.osfamily = 'osfamily'
		self.properties = {self.rootdir:self.dirname, self.osfamily:OSFAMILY}
		
		if not os.path.exists(self.xmlfile):
			raise Exception, "Unable to find supplied project file \"%s\"" % self.xmlfile
		
		try:
			self.doc = xml.dom.minidom.parse(self.xmlfile)
		except:
			raise Exception, sys.exc_info()[1]
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

			elif propertyNode.hasAttribute("root"):
				self.properties.pop(self.rootdir, "")
				self.rootdir = propertyNode.getAttribute("root")
				self.properties[self.rootdir] = self.dirname
			
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
					if regex.search(line) is not None:
						name = re.match(regex, line).group('name')
						value = re.match(regex, line).group('value')					
						value = self.expandFromProperty(value, "")				
						self.properties[name.strip()] = value.strip()


	def expandFromEnvironent(self, value, default):
		regex = re.compile(PROPERTY_EXPAND_ENV%self.environment, re.M)
		while regex.search(value) is not None:
			matches = regex.findall(value)				
			for m in matches:
				try:
					insert = os.environ[m[1]]
				except Exception: # presumably a KeyError
					if default==value: # if even default can't be resolved avoid infinite loop and tell user
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
					# fall back to default, which we will then try to expand if necessary
					value = default
					break
				value = value.replace(m[0], insert)
		return value		


	def expandFromProperty(self, value, default):
		regex = re.compile(PROPERTY_EXPAND, re.M)
		while regex.search(value) is not None:
			matches = regex.findall(value)
			for m in matches:
				try:
					insert = self.properties[m[1]]
				except Exception: # presumably a KeyError
					if default==value: # if even default can't be resolved avoid infinite loop and tell user
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
					# fall back to default, which we will then try to expand if necessary
					value = default
					break
				value = value.replace(m[0], insert)
		return value


	def getRunnerDetails(self):
		try:
			runnerNodeList = self.root.getElementsByTagName('runner')[0]
			return [runnerNodeList.getAttribute('classname'), runnerNodeList.getAttribute('module')]
		except:
			return DEFAULT_RUNNER


	def getMakerDetails(self):
		try:
			makerNodeList = self.root.getElementsByTagName('maker')[0]
			return [makerNodeList.getAttribute('classname'), makerNodeList.getAttribute('module')]
		except:
			return DEFAULT_MAKER


	def setFormatters(self, formatters):
		formattersNodeList = self.root.getElementsByTagName('formatters')
		if formattersNodeList == []: return 
		
		try:
			formatterNodeList = formattersNodeList[0].getElementsByTagName('formatter')
			if formatterNodeList != []:
				for formatterNode in formatterNodeList:
					try:
						datefmt = ''
						name = formatterNode.getAttribute('name')
						messagefmt = formatterNode.getAttribute('messagefmt')
						if formatterNode.hasAttribute('datefmt'): datefmt = formatterNode.getAttribute('datefmt')
						setattr(formatters, name, logging.Formatter(messagefmt, datefmt))
					except:
						pass
			return
		except:
			return
		
		
	def getWriterDetails(self):
		writersNodeList = self.root.getElementsByTagName('writers')
		if writersNodeList == []: return [DEFAULT_WRITER]
		
		try:
			writers = []
			writerNodeList = writersNodeList[0].getElementsByTagName('writer')
			if writerNodeList != []:
				for writerNode in writerNodeList:
					try:
						file = writerNode.getAttribute('file') if writerNode.hasAttribute('file') else None
						writer = [writerNode.getAttribute('classname'), writerNode.getAttribute('module'), file, {}]
					except:
						pass
					else:
						propertyNodeList = writerNode.getElementsByTagName('property')
						for propertyNode in propertyNodeList:
							try:
								name = propertyNode.getAttribute("name") 
								value = self.expandFromEnvironent(propertyNode.getAttribute("value"), propertyNode.getAttribute("default"))
								writer[3][name] = self.expandFromProperty(value, propertyNode.getAttribute("default"))
							except:
								pass
						writers.append(writer)				
			else:
				writers.append(DEFAULT_WRITER)
			return writers
		except:
			return [DEFAULT_WRITER]
		

	def addToPath(self):		
		pathNodeList = self.root.getElementsByTagName('path')

		for pathNode in pathNodeList:
			try:
				value = self.expandFromEnvironent(pathNode.getAttribute("value"), "")
				value = self.expandFromProperty(value, "")
				relative = pathNode.getAttribute("relative")
		
				if relative == "true": value = os.path.join(self.dirname, value)
				sys.path.append(os.path.normpath(value))

			except:
				pass


	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()

