#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
The `Project <pysys.xml.project.Project>` class holds the ``pysysproject.xml`` project configuration, including all 
user-defined project properties. 

"""

__all__ = ['Project'] # Project is the only member we expose/document from this module

import os.path, logging, xml.dom.minidom, collections, codecs, time

from pysys.constants import *
from pysys import __version__
from pysys.utils.loader import import_module
from pysys.utils.logutils import ColorLogFormatter, BaseLogFormatter
from pysys.utils.stringutils import compareVersions
from pysys.utils.fileutils import mkdir
from pysys.utils.pycompat import openfile
from pysys.exceptions import UserError

log = logging.getLogger('pysys.xml.project')

DTD='''
<!DOCTYPE pysysproject [
<!ELEMENT pysysproject (property*, path*, requires-python?, requires-pysys?, runner?, maker?, writers?, default-file-encodings?, formatters?, performance-reporter?), collect-test-output*, project-help >
<!ELEMENT property (#PCDATA)>
<!ELEMENT path (#PCDATA)>
<!ELEMENT requires-python (#PCDATA)>
<!ELEMENT requires-pysys (#PCDATA)>
<!ELEMENT runner (#PCDATA)>
<!ELEMENT performance-reporter (property*)>
<!ELEMENT maker (#PCDATA)>
<!ELEMENT default-file-encodings (default-file-encoding+) >
<!ELEMENT formatters (formatter+) >
<!ELEMENT formatter (property*) >
<!ELEMENT project-help (#PCDATA)>
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
<!ATTLIST default-file-encoding pattern CDATA #REQUIRED>
<!ATTLIST default-file-encoding encoding CDATA #REQUIRED>
<!ATTLIST collect-test-output pattern outputDir outputPattern #REQUIRED>
]>
'''

PROPERTY_EXPAND_ENV = "(?P<replace>\${%s.(?P<key>.*?)})"
PROPERTY_EXPAND = "(?P<replace>\${(?P<key>.*?)})"


class XMLProjectParser(object):
	"""
	:meta private: Not public API. 
	"""
	def __init__(self, dirname, file):
		self.dirname = dirname
		self.xmlfile = os.path.join(dirname, file)
		log.debug('Loading project file: %s', self.xmlfile)
		self.rootdir = 'root'
		self.environment = 'env'
		self.osfamily = 'osfamily'
		
		# project load time is a reasonable proxy for test start time, 
		# and we might want to substitute the date/time into property values
		self.startTimestamp = time.time()
		
		self.properties = {
			self.rootdir:self.dirname, 
			self.osfamily:OSFAMILY, 
			'hostname':HOSTNAME.lower().split('.')[0],
			'startDate':time.strftime('%Y-%m-%d', time.gmtime(self.startTimestamp)),
			'startTime':time.strftime('%H.%M.%S', time.gmtime(self.startTimestamp)),
		}
		
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
				if compareVersions(requirespysys, thisversion) > 0:
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
				log.debug('Setting project property %s="%s"', self.rootdir, self.dirname)

			elif propertyNode.hasAttribute("osfamily"):
				self.properties.pop(self.osfamily, "")
				self.osfamily = propertyNode.getAttribute("osfamily")
				self.properties[self.osfamily] = OSFAMILY
				log.debug('Setting project property %s="%s"', self.osfamily, OSFAMILY)
					
			elif propertyNode.hasAttribute("file"): 
				file = self.expandFromProperty(propertyNode.getAttribute("file"), propertyNode.getAttribute("default"))
				self.getPropertiesFromFile(os.path.normpath(os.path.join(self.dirname, file)) if file else '', 
					pathMustExist=(propertyNode.getAttribute("pathMustExist") or '').lower()=='true')
			
			elif propertyNode.hasAttribute("name"):
				name = propertyNode.getAttribute("name") 
				value = self.expandFromEnvironent(propertyNode.getAttribute("value"), propertyNode.getAttribute("default"))
				self.properties[name] = value = self.expandFromProperty(value, propertyNode.getAttribute("default"))
				log.debug('Setting project property %s="%s"', name, value)

				if (propertyNode.getAttribute("pathMustExist") or '').lower()=='true':
					if not (value and os.path.exists(os.path.join(self.dirname, value))):
						raise UserError('Cannot find path referenced in project property "%s": "%s"'%(
							name, '' if not value else os.path.normpath(os.path.join(self.dirname, value))))

		return self.properties


	def getPropertiesFromFile(self, file, pathMustExist=False):
		if not os.path.isfile(file):
			if pathMustExist:
				raise UserError('Cannot find properties file referenced in %s: "%s"'%(
					self.xmlfile, file))

			log.debug('Skipping project properties file which not exist: "%s"', file)
			return

		with open(file, 'r') as fp:
			for line in fp:
				line = line.split('=', 1)
				if len(line) == 2:
					name, value = line[0], line[1]
					value = self.expandFromProperty(value, "")	
					name = name.strip()
					value = value.strip()
					self.properties[name] = value
					log.debug('Setting project property %s="%s" (from %s)', name, self.properties[name], file)


	def expandFromEnvironent(self, value, default):
		regex = re.compile(PROPERTY_EXPAND_ENV%self.environment, re.M)
		while regex.search(value) is not None:
			matches = regex.findall(value)				
			for m in matches:
				try:
					insert = os.environ[m[1]]
				except Exception:
					# this means that if the default also contains something that can't be resolved we get a hard failure 
					# (otherwise would stack overflow)
					if default==value:
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
					log.debug('Failed to expand property from environment variables; "%s" env var does not exist so using default "%s"', m[1], default)

					value = default
					break
				value = value.replace(m[0], insert)
				log.debug('Expanding project property from environment: %s->"%s"', m[0], insert)

		return value		


	def expandFromProperty(self, value, default):
		regex = re.compile(PROPERTY_EXPAND, re.M)
		while regex.search(value) is not None:
			matches = regex.findall(value)
			for m in matches:
				try:
					insert = self.properties[m[1]]
				except Exception as e:
					# this means that if the default also contains something that can't be resolved we get a hard failure 
					# (otherwise would stack overflow)
					if default==value:
						raise Exception('Cannot expand default property value "%s": cannot resolve %s'%(default or value, m[1]))
					log.debug('Failed to expand property %s in "%s" (will use default "%s") - %s: %s', m[1], value, default, e.__class__.__name__, e)
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


	def getCollectTestOutputDetails(self):
		r = []
		for n in self.root.getElementsByTagName('collect-test-output'):
			x = {
				'pattern':n.getAttribute('pattern'),
				'outputDir':self.expandFromProperty(n.getAttribute('outputDir'), n.getAttribute('outputDir')),
				'outputPattern':n.getAttribute('outputPattern'),
			}
			assert 'pattern' in x, x
			assert 'outputDir' in x, x
			assert 'outputPattern' in x, x
			assert '@UNIQUE@' in x['outputPattern'], 'collect-test-output outputPattern must include @UNIQUE@'
			r.append(x)
		return r


	def getPerformanceReporterDetails(self):
		nodeList = self.root.getElementsByTagName('performance-reporter')
		cls, optionsDict = self._parseClassAndConfigDict(nodeList[0] if nodeList else None, 'pysys.utils.perfreporter.CSVPerformanceReporter')
			
		summaryfile = optionsDict.pop('summaryfile', '')
		summaryfile = self.expandFromProperty(summaryfile, summaryfile)
		if optionsDict: raise Exception('Unexpected performancereporter attribute(s): '+', '.join(list(optionsDict.keys())))
		
		return cls, summaryfile

	def getProjectHelp(self):
		help = ''
		for e in self.root.getElementsByTagName('project-help'):
			for n in e.childNodes:
				if (n.nodeType in {e.TEXT_NODE,e.CDATA_SECTION_NODE}) and n.data:
					help += n.data
		return help

	def getDescriptorLoaderClass(self):
		nodeList = self.root.getElementsByTagName('descriptor-loader')
		cls, optionsDict = self._parseClassAndConfigDict(nodeList[0] if nodeList else None, 'pysys.xml.descriptor.DescriptorLoader')
		
		if optionsDict: raise Exception('Unexpected descriptor-loader attribute(s): '+', '.join(list(optionsDict.keys())))
		
		return cls

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

	def getDefaultFileEncodings(self):
		result = []
		for n in self.root.getElementsByTagName('default-file-encoding'):
			pattern = (n.getAttribute('pattern') or '').strip().replace('\\','/')
			encoding = (n.getAttribute('encoding') or '').strip()
			if not pattern: raise Exception('<default-file-encoding> element must include both a pattern= attribute')
			if encoding: 
				codecs.lookup(encoding) # give an exception if an invalid encoding is specified
			else:
				encoding=None
			result.append({'pattern':pattern, 'encoding':encoding})
		return result

	def getExecutionOrderHints(self):
		result = []
		secondaryModesHintDelta = None
		
		def makeregex(s):
			if not s: return None
			if s.startswith('!'): raise UserError('Exclusions such as !xxx are not permitted in execution-order configuration')
			
			# make a regex that will match either the entire expression as a literal 
			# or the entire expression as a regex
			s = s.rstrip('$')
			try:
				#return re.compile('(%s|%s)$'%(re.escape(s), s))
				return re.compile('%s$'%(s))
			except Exception as ex:
				raise UserError('Invalid regular expression in execution-order "%s": %s'%(s, ex))
		
		for parent in self.root.getElementsByTagName('execution-order'):
			if parent.getAttribute('secondaryModesHintDelta'):
				secondaryModesHintDelta = float(parent.getAttribute('secondaryModesHintDelta'))
			for n in parent.getElementsByTagName('execution-order'):
				moderegex = makeregex(n.getAttribute('forMode'))
				groupregex = makeregex(n.getAttribute('forGroup'))
				if not (moderegex or groupregex): raise UserError('Must specify either forMode, forGroup or both')
				
				hintmatcher = lambda groups, mode, moderegex=moderegex, groupregex=groupregex: (
					(moderegex is None or moderegex.match(mode or '')) and
					(groupregex is None or any(groupregex.match(group) for group in groups))
					)
				
				result.append( 
					(float(n.getAttribute('hint')), hintmatcher )
					)
		if secondaryModesHintDelta is None: 
			secondaryModesHintDelta = +100.0 # default value
		return result, secondaryModesHintDelta

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
		for elementname in ['path', 'pythonpath']:
			pathNodeList = self.root.getElementsByTagName(elementname)

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

		:param node: The node, may be None
		:param defaultClass: a string specifying the default fully-qualified class
		:return: a tuple of (pythonclassconstructor, propertiesdict)
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

		# defer importing the module until we actually need to instantiate the 
		# class, to avoid introducing tricky module import order problems, given 
		# that the project itself needs loading very early
		def classConstructor(*args, **kwargs):
			module = import_module(mod, sys.path)
			cls = getattr(module, classname)
			return cls(*args, **kwargs) # invoke the constructor for this class
		return classConstructor, optionsDict

def getProjectConfigTemplates():
	"""Get a list of available templates that can be used for creating a new project configuration. 
	
	:return: A dict, where each value is an absolute path to an XML template file 
		and each key is the display name for that template. 
	"""
	templatedir = os.path.dirname(__file__)+'/templates/project'
	templates = { t.replace('.xml',''): templatedir+'/'+t 
		for t in os.listdir(templatedir) if t.endswith('.xml')}
	assert templates, 'No project templates found in %s'%templatedir
	return templates

def createProjectConfig(targetdir, templatepath=None):
	"""Create a new project configuration file in the specified targetdir. 
	"""
	if not templatepath: templatepath = getProjectConfigTemplates()['default']
	mkdir(targetdir)
	# using ascii ensures we don't unintentionally add weird characters to the default (utf-8) file
	with openfile(templatepath, encoding='ascii') as src:
		with openfile(os.path.abspath(targetdir+'/'+DEFAULT_PROJECTFILE[0]), 'w', encoding='ascii') as target:
			for l in src:
				l = l.replace('@PYTHON_VERSION@', '%s.%s.%s'%sys.version_info[0:3])
				l = l.replace('@PYSYS_VERSION@', '.'.join(__version__.split('.')[0:3]))
				target.write(l)

class Project(object):
	"""Contains settings for the entire test project, as defined by the 
	``pysysproject.xml`` project configuration file.
	
	To get a reference to the current `Project` instance, use the 
	`pysys.basetest.BaseTest.project` 
	(or `pysys.process.user.ProcessUser.project`) field. 
	
	This class reads and parses the PySys project file if it exists and sets 
	an instance attribute for every::
	
	   <property name="PROP_NAME">prop value</property>
	
	element in the file. 
	
	:ivar dict(str,str) ~.properties: The resolved values of all project properties defined in the configuration file. 
		In addition, each of these is set as an attribute onto the `Project` instance itself. 
	:ivar str ~.root: Full path to the project root directory, as specified by the first PySys project
		file encountered when walking up the directory tree from the start directory. 
		If no project file was found, this is just the start directory PySys was run from.
	:ivar str ~.projectFile: Full path to the project file.  
	
	"""
	
	__INSTANCE = None
		
	def __init__(self, root, projectFile):
		self.root = root
		self.startTimestamp = time.time()
		self.runnerClassname, self.runnerModule = DEFAULT_RUNNER
		self.makerClassname, self.makerModule = DEFAULT_MAKER
		self.writers = [DEFAULT_WRITER]
		self.perfReporterConfig = None
		self.defaultFileEncodings = [] # ordered list where each item is a dictionary with pattern and encoding; first matching item wins
		self.collectTestOutput = []
		self.projectHelp = None
		self.properties = {}
		stdoutformatter, runlogformatter = None, None

		self.projectFile = None
		if projectFile is not None:
			if not os.path.exists(os.path.join(root, projectFile)):
				raise Exception("Project file not found: %s" % os.path.normpath(os.path.join(root, projectFile)))
			from pysys.xml.project import XMLProjectParser
			try:
				parser = XMLProjectParser(root, projectFile)
			except Exception as e: 
				raise Exception("Error parsing project file \"%s\": %s" % (os.path.join(root, projectFile),sys.exc_info()[1]))
			else:
				parser.checkVersions()
				self.projectFile = os.path.join(root, projectFile)
				
				self.startTimestamp = parser.startTimestamp
				
				# get the properties
				properties = parser.getProperties()
				keys = list(properties.keys())
				keys.sort()
				for key in keys: setattr(self, key, properties[key])
				self.properties = dict(properties)
				
				# add to the python path
				parser.addToPath()
		
				# get the runner if specified
				self.runnerClassname, self.runnerModule = parser.getRunnerDetails()
		
				# get the maker if specified
				self.makerClassname, self.makerModule = parser.getMakerDetails()

				# get the loggers to use
				self.writers = parser.getWriterDetails()

				self.perfReporterConfig = parser.getPerformanceReporterDetails()
				
				self.descriptorLoaderClass = parser.getDescriptorLoaderClass()

				# get the stdout and runlog formatters
				stdoutformatter, runlogformatter = parser.createFormatters()
				
				self.defaultFileEncodings = parser.getDefaultFileEncodings()
				
				self.executionOrderHints, self.executionOrderSecondaryModesHintDelta = parser.getExecutionOrderHints()
				
				self.collectTestOutput = parser.getCollectTestOutputDetails()
				
				self.projectHelp = parser.getProjectHelp()
				def expandProperty(m):
					m = m.group(1)
					if m == '$': return '$'
					return properties[m] # expand ${...} property in project help
				self.projectHelp = re.sub(r'[$][{]([^}]+)[}]', expandProperty, self.projectHelp)
				
				# set the data attributes
				parser.unlink()

		if not stdoutformatter: stdoutformatter = ColorLogFormatter({})
		if not runlogformatter: runlogformatter = BaseLogFormatter({})
		PySysFormatters = collections.namedtuple('PySysFormatters', ['stdout', 'runlog'])
		self.formatters = PySysFormatters(stdoutformatter, runlogformatter)

	@staticmethod
	def getInstance():
		"""
		Provides access to the singleton instance of Project.
		
		Raises an exception if the project has not yet been loaded.  
		
		Use ``self.project`` to get access to the project instance where possible, 
		for example from a `pysys.basetest.BaseTest` or `pysys.baserunner.BaseRunner` class. This attribute is for 
		use in internal functions and classes that do not have a ``self.project``.
		"""
		if Project.__INSTANCE: return Project.__INSTANCE
		if 'doctest' in sys.argv[0]: return None # special-case for doctesting
		raise Exception('Cannot call Project.getInstance() as the project has not been loaded yet')
	
	@staticmethod
	def findAndLoadProject(startdir):
		"""Find and load a project file, starting from the specified directory. 
		
		If this fails an error is logged and the process is terminated. 
		
		The method walks up the directory tree from the supplied path until the 
		PySys project file is found. The location of the project file defines
		the project root location. The contents of the project file determine 
		project specific constants as specified by property elements in the 
		xml project file.
		
		To ensure that all loaded modules have a pre-initialised projects 
		instance, any launching application should first import the loadproject
		file, and then make a call to it prior to importing all names within the
		constants module.

		:param startdir: The initial path to start from when trying to locate the project file

		"""
		projectFile = os.getenv('PYSYS_PROJECTFILE', None)
		search = startdir
		if not projectFile:
			projectFileSet = set(DEFAULT_PROJECTFILE)
			
			drive, path = os.path.splitdrive(search)
			while (not search == drive):
				intersection =  projectFileSet & set(os.listdir(search))
				if intersection : 
					projectFile = intersection.pop()
					break
				else:
					search, drop = os.path.split(search)
					if not drop: search = drive
		
			if not (projectFile is not None and os.path.exists(os.path.join(search, projectFile))): # pragma: no cover
				if os.getenv('PYSYS_PERMIT_NO_PROJECTFILE','').lower()=='true':
					sys.stderr.write("WARNING: No project file found; using default settings and taking project root to be '%s' \n" % (search or '.'))
				else:
					sys.stderr.write('\n'.join([
						#                                                                               |
						"WARNING: No PySys test project file exists in this directory (or its parents):",
						"  - If you wish to start a new project, begin by running 'pysys makeproject'.",
						"  - If you are trying to use an existing project, change directory to a ",
						"    location under the root test directory that contains your project file.",
						"  - If you wish to use an existing project that has no configuration file, ",
						"    set the PYSYS_PERMIT_NO_PROJECTFILE=true environment variable.",
						""
					]))
					sys.exit(1)

		try:
			project = Project(search, projectFile)
			stdoutHandler.setFormatter(project.formatters.stdout)
			Project.__INSTANCE = project # set singleton
			return project
		except UserError as e: 
			sys.stderr.write("ERROR: Failed to load project - %s"%e)
			sys.exit(1)
		except Exception as e:
			sys.stderr.write("ERROR: Failed to load project due to %s - %s\n"%(e.__class__.__name__, e))
			traceback.print_exc()
			sys.exit(1)
