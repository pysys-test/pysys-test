#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

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

import os.path, logging, xml.dom.minidom, collections

from pysys.constants import *
from pysys import __version__
from pysys.utils.loader import import_module
from pysys.utils.logutils import ColorLogFormatter, BaseLogFormatter
log = logging.getLogger('pysys.xml.project')

DTD='''
<!DOCTYPE pysysproject [
<!ELEMENT pysysproject (property*, path*, requires-python?, requires-pysys?, runner?, maker?, writers?, formatters?, performance-reporter?) >
<!ELEMENT property (#PCDATA)>
<!ELEMENT path (#PCDATA)>
<!ELEMENT requires-python (#PCDATA)>
<!ELEMENT requires-pysys (#PCDATA)>
<!ELEMENT runner (#PCDATA)>
<!ELEMENT performance-reporter (property*)>
<!ELEMENT maker (#PCDATA)>
<!ELEMENT formatters (formatter+) >
<!ELEMENT formatter (property*) >
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
<!ATTLIST performance-reporter classname CDATA #REQUIRED>
<!ATTLIST performance-reporter module CDATA #REQUIRED>
<!ATTLIST performance-reporter summaryfile CDATA #REQUIRED>
<!ATTLIST maker classname CDATA #REQUIRED>
<!ATTLIST maker module CDATA #REQUIRED>
<!ATTLIST formatter name CDATA #REQUIRED>
<!ATTLIST formatter messagefmt CDATA #IMPLIED>
<!ATTLIST formatter datefmt CDATA #IMPLIED>
<!ATTLIST formatter classname CDATA #IMPLIED>
<!ATTLIST formatter module CDATA #IMPLIED>
<!ATTLIST writer classname CDATA #REQUIRED>
<!ATTLIST writer module CDATA #REQUIRED>
<!ATTLIST writer file CDATA #IMPLIED>
]>
'''

PROPERTY_EXPAND_ENV = "(?P<replace>\${%s.(?P<key>.*?)})"
PROPERTY_EXPAND = "(?P<replace>\${(?P<key>.*?)})"
PROPERTY_FILE = "(?P<name>^.*)=(?P<value>.*)$"


class XMLProjectParser(object):
	def __init__(self, dirname, file):
		self.dirname = dirname
		self.xmlfile = os.path.join(dirname, file)
		self.rootdir = 'root'
		self.environment = 'env'
		self.osfamily = 'osfamily'
		self.properties = {self.rootdir:self.dirname, self.osfamily:OSFAMILY}
		
		if not os.path.exists(self.xmlfile):
			raise Exception("Unable to find supplied project file \"%s\"" % self.xmlfile)
		
		try:
			self.doc = xml.dom.minidom.parse(self.xmlfile)
		except Exception:
			raise Exception(sys.exc_info()[1])
		else:
			if self.doc.getElementsByTagName('pysysproject') == []:
				raise Exception("No <pysysproject> element supplied in project file")
			else:
				self.root = self.doc.getElementsByTagName('pysysproject')[0]


	def checkVersions(self):
		requirespython = self.root.getElementsByTagName('requires-python')
		if requirespython and requirespython[0].firstChild: 
			requirespython = requirespython[0].firstChild.nodeValue
			if requirespython:
				if list(sys.version_info) < list(map(int, requirespython.split('.'))):
					raise Exception('This test project requires Python version %s or greater, but this is version %s (from %s)'%(requirespython, '.'.join([str(x) for x in sys.version_info[:3]]), sys.executable))

		requirespysys = self.root.getElementsByTagName('requires-pysys')
		if requirespysys and requirespysys[0].firstChild: 
			requirespysys = requirespysys[0].firstChild.nodeValue
			if requirespysys:
				thisversion = __version__
				if list(map(int, thisversion.split('.'))) < list(map(int, requirespysys.split('.'))):
					raise Exception('This test project requires PySys version %s or greater, but this is version %s'%(requirespysys, thisversion))


	def unlink(self):
		if self.doc: self.doc.unlink()	


	def getProperties(self):
		propertyNodeList = [element for element in self.root.getElementsByTagName('property') if element.parentNode == self.root]

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
			except Exception: 
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
				except Exception:
					if default==value:
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
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
				except Exception as e:
					log.debug('Failed to expand properties in "%s" - %s: %s', value, e.__class__.__name__, e)
					if default==value:
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
					value = default
					break
				value = value.replace(m[0], insert)
		return value


	def getRunnerDetails(self):
		try:
			runnerNodeList = self.root.getElementsByTagName('runner')[0]
			return [runnerNodeList.getAttribute('classname'), runnerNodeList.getAttribute('module')]
		except Exception:
			return DEFAULT_RUNNER


	def getPerformanceReporterDetails(self):
		nodeList = self.root.getElementsByTagName('performance-reporter')
		cls, optionsDict = self._parseClassAndConfigDict(nodeList[0] if nodeList else None, 'pysys.utils.perfreporter.CSVPerformanceReporter')
			
		summaryfile = optionsDict.pop('summaryfile', '')
		summaryfile = self.expandFromProperty(summaryfile, summaryfile)
		if optionsDict: raise Exception('Unexpected performancereporter attribute(s): '+', '.join(list(optionsDict.keys())))
		
		return cls, summaryfile


	def getMakerDetails(self):
		try:
			makerNodeList = self.root.getElementsByTagName('maker')[0]
			return [makerNodeList.getAttribute('classname'), makerNodeList.getAttribute('module')]
		except Exception:
			return DEFAULT_MAKER


	def createFormatters(self):
		stdout = runlog = None
		
		formattersNodeList = self.root.getElementsByTagName('formatters')
		if formattersNodeList:
			formattersNodeList = formattersNodeList[0].getElementsByTagName('formatter')
		if formattersNodeList:
			for formatterNode in formattersNodeList:
				fname = formatterNode.getAttribute('name')
				if fname not in ['stdout', 'runlog']:
					raise Exception('Formatter "%s" is invalid - must be stdout or runlog'%fname)

				if fname == 'stdout':
					cls, options = self._parseClassAndConfigDict(formatterNode, 'pysys.utils.logutils.ColorLogFormatter')
					stdout = cls(options)
				else:
					cls, options = self._parseClassAndConfigDict(formatterNode, 'pysys.utils.logutils.BaseLogFormatter')
					runlog = cls(options)
		return stdout, runlog


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
					except Exception:
						pass
					else:
						propertyNodeList = writerNode.getElementsByTagName('property')
						for propertyNode in propertyNodeList:
							try:
								name = propertyNode.getAttribute("name") 
								value = self.expandFromEnvironent(propertyNode.getAttribute("value"), propertyNode.getAttribute("default"))
								writer[3][name] = self.expandFromProperty(value, propertyNode.getAttribute("default"))
							except Exception:
								pass
						writers.append(writer)				
			else:
				writers.append(DEFAULT_WRITER)
			return writers
		except Exception:
			return [DEFAULT_WRITER]
		

	def addToPath(self):		
		pathNodeList = self.root.getElementsByTagName('path')

		for pathNode in pathNodeList:
				raw = self.expandFromEnvironent(pathNode.getAttribute("value"), "")
				value = self.expandFromProperty(raw, "")
				relative = pathNode.getAttribute("relative")
				if not value: 
					log.warn('Cannot add directory to the python <path>: "%s"', raw)
					continue

				if relative == "true": value = os.path.join(self.dirname, value)
				value = os.path.normpath(value)
				if not os.path.isdir(value): 
					log.warn('Cannot add non-existent directory to the python <path>: "%s"', value)
				else:
					log.debug('Adding value to path ')
					sys.path.append(value)


	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()


	def _parseClassAndConfigDict(self, node, defaultClass):
		"""Parses a dictionary of arbitrary options and a python class out of the specified XML node.

		The node may optionally contain classname and module (if not specified as a separate attribute,
		module will be extracted from the first part of classname); any other attributes will be returned in
		the optionsDict, as will <option name=""></option> child elements.

		@param node: The node, may be None
		@param defaultClass: a string specifying the default fully-qualified class
		@return: a tuple of (pythonclass, propertiesdict)
		"""
		optionsDict = {}
		if node:
			for att in range(node.attributes.length):
				value = self.expandFromEnvironent(node.attributes.item(att).value, None)
				optionsDict[node.attributes.item(att).name] = self.expandFromProperty(value, None)
			for tag in node.getElementsByTagName('property'):
				assert tag.getAttribute('name')
				value = self.expandFromEnvironent(tag.getAttribute("value"), tag.getAttribute("default"))
				optionsDict[tag.getAttribute('name')] = self.expandFromProperty(value, tag.getAttribute("default"))

		classname = optionsDict.pop('classname', defaultClass)
		mod = optionsDict.pop('module', '.'.join(classname.split('.')[:-1]))
		classname = classname.split('.')[-1]
		module = import_module(mod, sys.path)
		cls = getattr(module, classname)
		return cls, optionsDict


class Project(object):
	"""Class detailing project specific information for a set of PySys tests.
	
	Reads and parses the PySys project file if it exists and translates property element 
	name/value entries in the project file into data attributes of the class instance. 
	
	@ivar root: Full path to the project root, as specified by the first PySys project
				file encountered when walking down the directory tree from the start directory  
	@type root: string
	@ivar projectFile: Full path to the project file. May be None, though providing a file is recommended. 
	@type projectFile: string
	
	"""
	
	def __init__(self, root, projectFile):
		self.root = root

		self.runnerClassname, self.runnerModule = DEFAULT_RUNNER
		self.makerClassname, self.makerModule = DEFAULT_MAKER
		self.writers = [DEFAULT_WRITER]
		self.perfReporterConfig = None

		stdoutformatter, runlogformatter = None, None

		self.projectFile = None
		if projectFile is not None and os.path.exists(os.path.join(root, projectFile)):
			from pysys.xml.project import XMLProjectParser
			try:
				parser = XMLProjectParser(root, projectFile)
			except Exception as e: 
				raise Exception("Error parsing project file \"%s\": %s" % (os.path.join(root, projectFile),sys.exc_info()[1]))
			else:
				parser.checkVersions()
				self.projectFile = os.path.join(root, projectFile)
				
				# get the properties
				properties = parser.getProperties()
				keys = list(properties.keys())
				keys.sort()
				for key in keys: setattr(self, key, properties[key])
				
				# add to the python path
				parser.addToPath()
		
				# get the runner if specified
				self.runnerClassname, self.runnerModule = parser.getRunnerDetails()
		
				# get the maker if specified
				self.makerClassname, self.makerModule = parser.getMakerDetails()

				# get the loggers to use
				self.writers = parser.getWriterDetails()

				self.perfReporterConfig = parser.getPerformanceReporterDetails()

				# get the stdout and runlog formatters
				stdoutformatter, runlogformatter = parser.createFormatters()
				
				# set the data attributes
				parser.unlink()

		if not stdoutformatter: stdoutformatter = ColorLogFormatter({})
		if not runlogformatter: runlogformatter = BaseLogFormatter({})
		PySysFormatters = collections.namedtuple('PySysFormatters', ['stdout', 'runlog'])
		self.formatters = PySysFormatters(stdoutformatter, runlogformatter)