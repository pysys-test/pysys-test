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
The `Project <pysys.config.project.Project>` class holds the ``pysysproject.xml`` project configuration, including all 
user-defined project properties. 

"""

__all__ = ['Project'] # Project is the only member we expose/document from this module

import os.path, logging, xml.dom.minidom, collections, codecs, time
import platform
import locale
import getpass

import pysys
import pysys.utils.misc
from pysys.constants import *
from pysys import __version__
from importlib import import_module
from pysys.utils.logutils import ColorLogFormatter, BaseLogFormatter
from pysys.utils.fileutils import mkdir, loadProperties
from pysys.utils.pycompat import openfile, makeReadOnlyDict
from pysys.exceptions import UserError
import pysys.config.descriptor

log = logging.getLogger('pysys.config.project')

class _XMLProjectParser(object):
	"""
	:meta private: Not public API. 
	"""
	def __init__(self, dirname, file, outdir):
		self.dirname = dirname
		self.xmlfile = os.path.join(dirname, file)
		log.debug('Loading project file: %s', self.xmlfile)
		self.environment = 'env'
		
		# project load time is a reasonable proxy for test start time, 
		# and we might want to substitute the date/time into property values
		self.startTimestamp = time.time()
		
		try:
			username = os.getenv('PYSYS_USERNAME') or getpass.getuser().lower() # getpass throws if no env var is set to help with this
		except Exception as ex:
			username = 'UNKNOWN_USER'
		
		self.properties = {
			'testRootDir':self.dirname,
			
			'outDirName':os.path.basename(outdir),
			
			'startDate':time.strftime('%Y-%m-%d', time.localtime(self.startTimestamp)),
			'startTime':time.strftime('%H.%M.%S', time.localtime(self.startTimestamp)),
			'startTimeSecs':'%0.3f'%self.startTimestamp,

			'hostname':HOSTNAME.lower().split('.')[0],
			'os':platform.system().lower(), # e.g. 'windows', 'linux', 'darwin'; a more modern alternative to OSFAMILY
			'osfamily':OSFAMILY, # windows or unix
			
			'pysysTemplatesDir': os.path.dirname(__file__)+os.sep+'templates',
			'username': username,
			
			'/': os.sep, # so people can write strings like foo${/}bar and get a forward or back-slash depending on platform

			# old names
			'root':self.dirname, # old name for testRootDir
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
					raise UserError('This test project requires Python version %s or greater, but this is version %s (from %s)'%(requirespython, '.'.join([str(x) for x in sys.version_info[:3]]), sys.executable))

		requirespysys = self.root.getElementsByTagName('requires-pysys')
		if requirespysys and requirespysys[0].firstChild: 
			requirespysys = requirespysys[0].firstChild.nodeValue
			if requirespysys:
				thisversion = __version__
				if pysys.utils.misc.compareVersions(requirespysys, thisversion) > 0:
					raise UserError('This test project requires PySys version %s or greater, but this is version %s'%(requirespysys, thisversion))


	def unlink(self):
		if self.doc: self.doc.unlink()	


	def getProperties(self):
		propertyNodeList = [element for element in self.root.getElementsByTagName('property') if element.parentNode == self.root]

		for propertyNode in propertyNodeList:
			permittedAttributes = None
			# use of these options for customizing the property names of env/root/osfamily is no longer encouraged; just kept for compat
			if propertyNode.hasAttribute("environment"):
				self.environment = propertyNode.getAttribute("environment")
			elif propertyNode.hasAttribute("root"): 
				propname = propertyNode.getAttribute("root")
				self.properties[propname] = self.dirname
				log.debug('Setting project property %s="%s"', propname, self.dirname)
			elif propertyNode.hasAttribute("osfamily"): # just for older configs, better to use ${os} now
				propname = propertyNode.getAttribute("osfamily")
				self.properties[propname] = OSFAMILY
				log.debug('Setting project property %s="%s"', propname, OSFAMILY)
					
			elif propertyNode.hasAttribute("file"): 
				file = self.expandProperties(propertyNode.getAttribute("file"), default=propertyNode, name='properties file reading')
				self.getPropertiesFromFile(os.path.normpath(os.path.join(self.dirname, file)) if file else '', 
					pathMustExist=(propertyNode.getAttribute("pathMustExist") or '').lower()=='true',
					includes=propertyNode.getAttribute("includes"),
					excludes=propertyNode.getAttribute("excludes"),
					prefix=propertyNode.getAttribute("prefix") or '',
					)
				permittedAttributes = {'name', 'file', 'default', 'pathMustExist', 'includes', 'excludes', 'prefix'}

			elif propertyNode.hasAttribute("name"):
				name = propertyNode.getAttribute("name") 
				value = self.expandProperties(
						propertyNode.getAttribute("value")
						or '\n'.join(n.data for n in propertyNode.childNodes 
							if (n.nodeType in {n.TEXT_NODE,n.CDATA_SECTION_NODE}) and n.data), 
					default=propertyNode, name=name)
				if name in self.properties:
					raise UserError('Cannot set project property "%s" as it is already set'%name)

				if (propertyNode.getAttribute("pathMustExist") or '').lower()=='true':
					if not (value and os.path.exists(os.path.join(self.dirname, value))):
						raise UserError('Cannot find path referenced in project property "%s": "%s"'%(
							name, '' if not value else os.path.normpath(os.path.join(self.dirname, value))))
					value = os.path.normpath(value) # since we know it's a path, make it a nice one

				self.properties[name] = value
				log.debug('Setting project property %s="%s"', name, value)

				permittedAttributes = {'name', 'value', 'default', 'pathMustExist'}
			else:
				raise UserError('Found <property> with no name= or file=')
			
			if permittedAttributes is not None:
				for att in range(propertyNode.attributes.length):
					attName = propertyNode.attributes.item(att).name
					if attName not in permittedAttributes: 
						# not an error, to allow for adding new ones in future pysys versions, but worth warning about
						log.warning('Unknown <property> attribute "%s" in project configuration'%attName)

		return self.properties



	def getPropertiesFromFile(self, file, pathMustExist=False, includes=None, excludes=None, prefix=''):
		if not os.path.isfile(file):
			if pathMustExist:
				raise UserError('Cannot find properties file referenced in %s: "%s"'%(
					self.xmlfile, file))

			log.debug('Skipping project properties file which not exist: "%s"', file)
			return

		try:
			rawProps = loadProperties(file) # since PySys 1.6.0 this is UTF-8 by default
		except UnicodeDecodeError:
			# fall back to ISO8859-1 if not valid UTF-8 (matching Java 9+ behaviour)
			rawProps = loadProperties(file, encoding='iso8859-1')
		
		props = collections.OrderedDict()
		for name, value in rawProps.items():
			if includes and not re.match(includes, name): continue
			if excludes and re.match(excludes, name): continue
			props[prefix+name] = value
				
		for name, value in props.items():
			# when loading properties files it's not so helpful to give errors (and there's nowhere else to put an empty value) so default to empty string
			value = self.expandProperties(value, default='', name=name)	
			
			if name in self.properties and value != self.properties[name]:
				# Whereas we want a hard error for duplicate <property name=".../> entries, for properties files 
				# there's a good case to allow overwriting of properties, but it log it at INFO
				log.info('Overwriting previous value of project property "%s" with new value "%s" from "%s"'%(name, value, os.path.basename(file)))

			self.properties[name] = value
			log.debug('Setting project property %s="%s" (from %s)', name, self.properties[name], file)

	def expandProperties(self, value, default, name=None):
		"""
		Expand any ${...} project properties or env vars, with ${$} for escaping.
		The "default" is expanded and used if value contains some undefined variables. 
		If default=None then an error is raised instead. If default is a node, its "default" attribute is used
		
		The "name" is used to generate more informative error messages
		"""
		envprefix = self.environment+'.'
		errorprefix = ('Error setting project property "%s": '%name) if name else ''
		
		if hasattr(default, 'getAttribute'):
			default = default.getAttribute("default") if default.hasAttribute("default") else None

		def expandProperty(m):
			m = m.group(1)
			if m == '$': return '$'
			try:
				if m.startswith(envprefix): 
					return os.environ[m[len(envprefix):]]
				if m.startswith('env:'): # for consistency with eval: also support this syntax
					return os.environ[m[4:]]
			except KeyError as ex:
				raise KeyError(errorprefix+'cannot find environment variable "%s"'%m[len(envprefix):])
			
			if m.startswith('eval:'):
				props = dict(self.properties)
				props.pop('os', None) # remove this to avoid hiding the os.path module
				props['properties'] = self.properties
				try:
					v = pysys.utils.safeeval.safeEval(m[5:], extraNamespace=props, 
						errorMessage='Failed to evaluate Python eval() string "{expr}" during property expansion due to {error}')
					return str(v)
				except Exception as ex:
					raise UserError(str(ex))

			if m in self.properties:
				return self.properties[m]
			else:
				raise KeyError(errorprefix+'PySys project property ${%s} is not defined, please check your pysysproject.xml file"'%m)
		try:
			return re.sub(r'[$][{]([^}]+)[}]', expandProperty, value)
		except KeyError as ex:
			if default is None: raise UserError('%s; if this is intended to be an optional property please add a default="..." value'%ex)
			log.debug('Failed to resolve value "%s" of property "%s", so falling back to default value', value, name or '<unknown>')
			return re.sub(r'[$][{]([^}]+)[}]', expandProperty, default)

	def getRunnerDetails(self):
		nodes = self.root.getElementsByTagName('runner')
		if not nodes: return DEFAULT_RUNNER
		classname, propertiesdict = self._parseClassAndConfigDict(nodes[0], None, returnClassAsName=True)
		assert not propertiesdict, 'Properties are not supported under <runner>'
		return classname

	def getCollectTestOutputDetails(self):
		r = []
		for n in self.root.getElementsByTagName('collect-test-output'):
			x = {
				'pattern':n.getAttribute('pattern'),
				'outputDir':self.expandProperties(n.getAttribute('outputDir'), default=None, name='collect-test-output outputDir'),
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
		summaryfile = self.expandProperties(summaryfile, default=None, name='performance-reporter summaryfile')
		if optionsDict: raise UserError('Unexpected performancereporter attribute(s): '+', '.join(list(optionsDict.keys())))
		
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
		cls, optionsDict = self._parseClassAndConfigDict(nodeList[0] if nodeList else None, 'pysys.config.descriptor.DescriptorLoader')
		
		if optionsDict: raise UserError('Unexpected descriptor-loader attribute(s): '+', '.join(list(optionsDict.keys())))
		
		return cls

	def getTestPlugins(self):
		plugins = []
		for node in self.root.getElementsByTagName('test-plugin'):
			cls, optionsDict = self._parseClassAndConfigDict(node, None)
			alias = optionsDict.pop('alias', None)
			plugins.append( (cls, alias, optionsDict) )
		return plugins
		
	def getRunnerPlugins(self):
		plugins = []
		for node in self.root.getElementsByTagName('runner-plugin'):
			cls, optionsDict = self._parseClassAndConfigDict(node, None)
			alias = optionsDict.pop('alias', None)
			plugins.append( (cls, alias, optionsDict) )
		return plugins

	def getDescriptorLoaderPlugins(self):
		plugins = []
		for node in self.root.getElementsByTagName('descriptor-loader-plugin'):
			cls, optionsDict = self._parseClassAndConfigDict(node, None)
			plugins.append( (cls, optionsDict) )
		return plugins

	def getMakerDetails(self):
		nodes = self.root.getElementsByTagName('maker')
		if not nodes: return DEFAULT_MAKER
		classname, propertiesdict = self._parseClassAndConfigDict(nodes[0], None, returnClassAsName=True)
		assert not propertiesdict, 'Properties are not supported under <maker>'
		return classname
	
	def createFormatters(self):
		stdout = runlog = None
		
		formattersNodeList = self.root.getElementsByTagName('formatters')
		if formattersNodeList:
			formattersNodeList = formattersNodeList[0].getElementsByTagName('formatter')
		if formattersNodeList:
			for formatterNode in formattersNodeList:
				fname = formatterNode.getAttribute('name')
				if fname not in ['stdout', 'runlog']:
					raise UserError('Formatter "%s" is invalid - must be stdout or runlog'%fname)

				if fname == 'stdout':
					cls, options = self._parseClassAndConfigDict(formatterNode, 'pysys.utils.logutils.ColorLogFormatter')
					options['__formatterName'] = 'stdout'
					stdout = cls(options)
				else:
					cls, options = self._parseClassAndConfigDict(formatterNode, 'pysys.utils.logutils.BaseLogFormatter')
					options['__formatterName'] = 'runlog'
					runlog = cls(options)
		return stdout, runlog

	def getDefaultFileEncodings(self):
		result = []
		for n in self.root.getElementsByTagName('default-file-encoding'):
			pattern = (n.getAttribute('pattern') or '').strip().replace('\\','/')
			encoding = (n.getAttribute('encoding') or '').strip()
			if not pattern: raise UserError('<default-file-encoding> element must include both a pattern= attribute')
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
		# writers can optionally be under a 'writers' parent node but this is now optional, to facilitate 
		# a third party plugin vendor providing a snippet of a few consecutive lines to paste into the project config 
		# to enable new functionality
		writers = []
		writerNodeList = self.root.getElementsByTagName('writer')
		if not writerNodeList: return []
		for writerNode in writerNodeList:
			pythonclassconstructor, propertiesdict = self._parseClassAndConfigDict(writerNode, None)
			writers.append( (pythonclassconstructor, propertiesdict) )
		return writers

	def addToPath(self):		
		for elementname in ['path', 'pythonpath']:
			pathNodeList = self.root.getElementsByTagName(elementname)

			for pathNode in pathNodeList:
					value = self.expandProperties(pathNode.getAttribute("value"), default=None, name='pythonpath')
					if not value: 
						raise UserError('Cannot add directory to the pythonpath: "%s"'%value)

					# we ignore the "relative" option and always make it relative to the testrootdir if not already absolute
					value = os.path.join(self.dirname, value)
					value = os.path.normpath(value)
					if not os.path.isdir(value): 
						raise UserError('Cannot add non-existent directory to the python <path>: "%s"'%value)
					else:
						log.debug('Adding value to path: %s', value)
						sys.path.append(value)


	def writeXml(self):
		f = open(self.xmlfile, 'w')
		f.write(self.doc.toxml())
		f.close()


	def _parseClassAndConfigDict(self, node, defaultClass, returnClassAsName=False):
		"""Parses a dictionary of arbitrary options and a python class out of the specified XML node.

		The node may optionally contain classname and module (if not specified as a separate attribute,
		module will be extracted from the first part of classname); any other attributes will be returned in
		the optionsDict, as will <property name=""></property> child elements.

		:param node: The node, may be None
		:param defaultClass: a string specifying the name of the default fully-qualified class, if any
		:return: a tuple of (pythonclassconstructor, propertiesdict), or if returnClassAsName (classname, propertiesDict)
		"""
		optionsDict = {}
		if node:
			for att in range(node.attributes.length):
				name = node.attributes.item(att).name.strip()
				if name in optionsDict: raise UserError('Duplicate property "%s" in <%s> configuration'%(name, node.tagName))
				optionsDict[name] = self.expandProperties(node.attributes.item(att).value, default=None, name=name)
			for tag in node.getElementsByTagName('property'):
				name = tag.getAttribute('name')
				assert name
				if name in optionsDict: raise UserError('Duplicate property "%s" in <%s> configuration'%(name, node.tagName))
				optionsDict[name] = self.expandProperties(
					tag.getAttribute("value") or '\n'.join(n.data for n in tag.childNodes 
							if (n.nodeType in {n.TEXT_NODE,n.CDATA_SECTION_NODE}) and n.data),
					default=tag, name=name)
		classname = optionsDict.pop('classname', defaultClass)
		if not classname: raise UserError('Missing require attribute "classname=" for <%s>'%node.tagName)
		mod = optionsDict.pop('module', '.'.join(classname.split('.')[:-1]))
		classname = classname.split('.')[-1]

		if returnClassAsName:
			return (mod+'.'+classname).strip('.'), optionsDict

		# defer importing the module until we actually need to instantiate the 
		# class, to avoid introducing tricky module import order problems, given 
		# that the project itself needs loading very early
		def classConstructor(*args, **kwargs):
			module = import_module(mod)
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
				l = l.replace('@PYSYS_VERSION@', '.'.join(__version__.split('.')[0:2]))
				target.write(l)

class Project(object):
	"""Contains settings for the entire test project, as defined by the 
	``pysysproject.xml`` project configuration file; see :doc:`/pysys/ProjectConfiguration`.
	
	To get a reference to the current `Project` instance, use the 
	`pysys.basetest.BaseTest.project` 
	(or `pysys.process.user.ProcessUser.project`) field. 
	
	All project properties are strings. If you need to get a project property value that's a a bool/int/float/list it is 
	recommended to use `getProperty()` which will automatically perform the conversion. For string properties 
	you can just use ``project.propName`` or ``project.properties['propName']``. 
	
	:ivar dict(str,str) ~.properties: The resolved values of all project properties defined in the configuration file. 
		In addition, each of these is set as an attribute onto the `Project` instance itself. 
	:ivar str ~.root: Full path to the project root directory, as specified by the first PySys project
		file encountered when walking up the directory tree from the start directory. 
		If no project file was found, this is just the start directory PySys was run from.
	:ivar str ~.projectFile: Full path to the project file.  
	
	"""
	
	__INSTANCE = None
	__frozen = False
	
	def __init__(self, root, projectFile, outdir=None):
		assert projectFile
		self.root = root
		if not outdir: outdir = DEFAULT_OUTDIR

		if not os.path.exists(os.path.join(root, projectFile)):
			raise UserError("Project file not found: %s" % os.path.normpath(os.path.join(root, projectFile)))
		try:
			parser = _XMLProjectParser(root, projectFile, outdir=outdir)
		except UserError:
			raise
		except Exception as e: 
			raise Exception("Error parsing project file \"%s\": %s" % (os.path.join(root, projectFile),sys.exc_info()[1]))

		parser.checkVersions()
		self.projectFile = os.path.join(root, projectFile)
		
		self.startTimestamp = parser.startTimestamp
		
		# get the properties
		properties = parser.getProperties()
		keys = list(properties.keys())
		keys.sort()
		for key in keys: 
			if not hasattr(self, key): # don't overwrite existing props; people will have to use .getProperty() to access them
				setattr(self, key, properties[key])
		self.properties = dict(properties)
		
		# add to the python path
		parser.addToPath()

		# get the runner if specified
		self.runnerClassname = parser.getRunnerDetails()

		# get the maker if specified
		self.makerClassname = parser.getMakerDetails()

		self.writers = parser.getWriterDetails()
		self.testPlugins = parser.getTestPlugins()
		self.runnerPlugins = parser.getRunnerPlugins()
		self._descriptorLoaderPlugins = parser.getDescriptorLoaderPlugins()

		self.perfReporterConfig = parser.getPerformanceReporterDetails()
		
		self.descriptorLoaderClass = parser.getDescriptorLoaderClass()

		# get the stdout and runlog formatters
		stdoutformatter, runlogformatter = parser.createFormatters()
		
		self.defaultFileEncodings = parser.getDefaultFileEncodings()
		
		self.executionOrderHints, self.executionOrderSecondaryModesHintDelta = parser.getExecutionOrderHints()
		
		self.collectTestOutput = parser.getCollectTestOutputDetails()
		
		self.projectHelp = parser.getProjectHelp()
		self.projectHelp = parser.expandProperties(self.projectHelp, default=None, name='project-help')
		
		self._defaultDirConfig = None # this field is not public API
		e = parser.root.getElementsByTagName('pysysdirconfig')
		assert len(e) <= 1, 'Cannot have more than one pysysdirconfig element in pysysproject.xml'
		if e:
			self._defaultDirConfig = pysys.config.descriptor._XMLDescriptorParser.parse(self.projectFile, istest=False, 
				project=self, xmlRootElement=e[0])
		
		# set the data attributes
		parser.unlink()
		
		if not stdoutformatter: stdoutformatter = ColorLogFormatter({'__formatterName':'stdout'})
		if not runlogformatter: runlogformatter = BaseLogFormatter({'__formatterName':'runlog'})
		PySysFormatters = collections.namedtuple('PySysFormatters', ['stdout', 'runlog'])
		self.formatters = PySysFormatters(stdoutformatter, runlogformatter)
		
		# for safety (test independence, and thread-safety), make it hard for people to accidentally edit project properties later
		self.properties = makeReadOnlyDict(self.properties)
		self.__frozen = True

	def __setattr__(self, name, value):
		if self.__frozen: raise Exception('Project cannot be modified after it has been loaded (use the runner to store global state if needed)')
		object.__setattr__(self, name, value)

	def expandProperties(self, value):
		"""
		Expand any ${...} project properties in the specified string. 
		
		An exception is thrown if any property is missing. This method is only for expanding project properties 
		and ``${eval:xxx})`` strings, so ``${env.*}`` syntax is not permitted (if you need to use an environment 
		variable, put it into a project property first). 
		
		.. versionadded:: 1.6.0
		
		:param str value: The string in which any properties will be expanded. ${$} can be used for escaping a literal $ if needed. 
		:return str: The value with properties expanded, or None if value=None. 
		"""
		if (not value) or ('${' not in value): return value
		
		def expandProperty(m):
			m = m.group(1)
			if m == '$': return '$'
	
			if m.startswith('eval:'):
				props = dict(self.properties)
				props.pop('os', None) # remove this to avoid hiding the os.path module
				props['properties'] = self.properties
				try:
					v = pysys.utils.safeeval.safeEval(m[5:], extraNamespace=props, errorMessage='{error}')
					return str(v)
				except Exception as ex:
					raise Exception('Error resolving ${%s} eval() string: %s'%(m, ex))
			return self.properties[m]
		
		try:
			return re.sub(r'[$][{]([^}]+)[}]', expandProperty, value)
		except KeyError as ex:
			# A more informative error, but not a UserError since we don't have the context of where it was called from
			raise Exception('Cannot resolve project property %s in: %s'%(ex, value))

	def getProperty(self, key, default):
		"""
		Get the specified project property value, or a default if it is not defined, with type conversion from string 
		to int/float/bool/list[str] (matching the default's type; for list[str], comma-separated input is assumed). 

		.. versionadded:: 1.6.0
		
		:param str key: The name of the property.
		:param bool/int/float/str/list[str] default: The default value to return if the property is not set. 
			The type of the default parameter will be used to convert the property value from a string if it is 
			provided. An exception will be raised if the value is non-empty but cannot be converted to the indicated type. 
		"""
		return pysys.utils.misc.getTypedValueOrDefault(key, self.properties.get(key, None), default)

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
	def findAndLoadProject(startdir=None, outdir=None):
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

		:param st rstartdir: The initial path to start from when trying to locate the project file
		:param str outdir: The output directory specified on the command line. Some project properties may depend on 
			this. 

		"""
		projectFile = os.getenv('PYSYS_PROJECTFILE', None)
		search = startdir or os.getcwd()
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
		
			if not projectFile or not os.path.exists(os.path.join(search, projectFile)): # pragma: no cover
				if os.getenv('PYSYS_PERMIT_NO_PROJECTFILE','').lower()=='true':
					sys.stderr.write('FATAL ERROR: The PYSYS_PERMIT_NO_PROJECTFILE environment variable is no longer supported - you must create a pysysproject.xml file for your project')
					sys.exit(1)
				else:
					sys.stderr.write('\n'.join([
						#                                                                               |
						"WARNING: No PySys test project file exists in this directory (or its parents):",
						"  - If you wish to start a new project, begin by running 'pysys makeproject'.",
						"  - If you are trying to use an existing project, change directory to a ",
						"    location under the directory that contains your project file.",
						""
					]))
					sys.exit(1)

		try:
			project = Project(search, projectFile, outdir=outdir)
			stdoutHandler.setFormatter(project.formatters.stdout)
			import pysys.constants
			pysys.constants.PROJECT = project # for compatibility for old tests
			Project.__INSTANCE = project # set singleton
			return project
		except UserError as e: 
			sys.stderr.write("ERROR: Failed to load project - %s"%e)
			sys.exit(1)
		except Exception as e:
			sys.stderr.write("ERROR: Failed to load project due to %s - %s\n"%(e.__class__.__name__, e))
			traceback.print_exc()
			sys.exit(1)

import pysys.utils.safeeval # down here to break circular dependency
