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
Implements ``pysys.py make`` to create new testcases. 
"""

from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json
import importlib
import glob
import shutil

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors
from pysys.config.project import Project
from pysys.exceptions import UserError
from pysys.utils.pycompat import openfile, PY2
from pysys.utils.fileutils import toLongPathSafe, pathexists, mkdir

class DefaultTestMaker(object):
	"""
	The default implementation of ``pysys.py make``, which creates tests and other assets using templates configurable 
	on a per-directory basis using ``pysysdirconfig.xml``.
	
	A subclass can be specified in the project if further customization is required using::
	
		<maker classname="myorg.MyTestMaker"/>

	"""
	
	__PYSYS_DEFAULT_TEMPLATES = [
	{
		'name': 'pysys-default-test',
		'description': 'a default empty PySys test',
		'isTest':True,
		'copy': [
			'${pysysTemplatesDir}/test/*',
		],
		'mkdir': [],
		'replace':[
			['@@CURRENT_USER@@', '${username}'],
			['@@CURRENT_DATE@@', '${startDate}'], # also allow @TEST_ID@ e.g. testid
		], 
	},
	{
		'name': 'pysys-dir-config',
		'description': 'a pysysdirconfig.xml file for customizing the defaults for tests under this directory',
		'isTest':False,
		'copy': [
			'${pysysTemplatesDir}/dirconfig/pysysdirconfig.xml',
		],
		'mkdir': [],
		'replace':[], 
	},
	]

	def __init__(self, name="make", **kwargs):
		self.name = name
		self.parentDir = os.getcwd()

	def getTemplates(self):
		project = Project.getInstance()
		projectroot = os.path.normpath(os.path.dirname(project.projectFile))
		dir = self.parentDir

		DIR_CONFIG_DESCRIPTOR = 'pysysdirconfig.xml'
		if not project.projectFile or not dir.startswith(projectroot):
			log.debug('Project file does not exist under "%s" so processing of %s files is disabled', dir, DIR_CONFIG_DESCRIPTOR)
			return None
 
		from pysys.config.descriptor import _XMLDescriptorParser # uses a non-public API, so please don't copy this into your own test maker

		# load any descriptors between the project dir up to (AND including) the dir we'll be walking
		searchdirsuffix = dir[len(projectroot)+1:].split(os.sep) if len(dir)>len(projectroot) else []
		
		DEFAULT_DESCRIPTOR = _XMLDescriptorParser.DEFAULT_DESCRIPTOR
		
		def expandAndValidateTemplate(t, defaults):
			if defaults is None: defaults = DEFAULT_DESCRIPTOR

			if t['name'].lower().replace('_','').replace(' ','') != t['name']: raise UserError( # enforce this to make them easy to type on cmd line, and consistent
				"Invalid template name \"%s\" - must be lowercase and use hyphens not underscores/spaces for separating words, in \"%s\""%(t['name'], source))
		
			source = t.get('source', None)
			if t['isTest']: 
				t['mkdir'].append(defaults.output)
				t['mkdir'].append(defaults.input)
				t['mkdir'].append(defaults.reference)
			
			t['copy'] = [os.path.normpath(os.path.join(os.path.dirname(source) if source else '', project.expandProperties(x).strip())) for x in t['copy']]
			copy = []
			for c in t['copy']:
				globbed = glob.glob(c)
				if not globbed:
					raise UserError('Cannot find any matching items for "%s" in maker template "%s" of %s'%(c, t['name'], source))
				for c in globbed:
					if not os.path.exists(c):
						raise UserError('Cannot find file or directory "%s" in maker template "%s" of %s'%(c, t['name'], source))
					copy.append(c)
			t['copy'] = copy
			
			t['replace'] = [(r1, project.expandProperties(r2)) for (r1,r2) in t['replace']]
			
			return t
		
		# start with the built-ins
		templates = [expandAndValidateTemplate(t, project._defaultDirConfig) for t in self.__PYSYS_DEFAULT_TEMPLATES]
		
		parentDirDefaults = None
		for i in range(len(searchdirsuffix)+1): # up to AND including dir
			if i == 0:
				currentdir = projectroot
			else:
				currentdir = projectroot+os.sep+os.sep.join(searchdirsuffix[:i])
			
			if pathexists(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR):
				parentDirDefaults = _XMLDescriptorParser.parse(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR, parentDirDefaults=parentDirDefaults, istest=False, project=project)
				newtemplates = [expandAndValidateTemplate(t, parentDirDefaults) for t in parentDirDefaults._makeTestTemplates]
				log.debug('Loaded directory configuration descriptor from %s: \n%s', currentdir, parentDirDefaults)
				
				# Add in existing templates from higher levels, but de-dup'd, giving priority to the latest defined template, and also putting the latest ones at the top of the list 
				# for increased prominence
				for deftmpl in templates:
					if not any(tmpl['name'] == deftmpl['name'] for tmpl in newtemplates):
						newtemplates.append(deftmpl) 
				templates = newtemplates

		log.debug('Loaded templates: \n%s', json.dumps(templates, indent='  '))
		return templates
		
	supportedArgs = ('ht:', ['help', 'template:'])

	def printOptions(self):
		#######                                                                                                                        |
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		print("\nUsage: %s %s [option]+ [-t TEMPLATE_NAME] [TESTID | -n]" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -h | --help                 print this message")
		# TODO: add -n - autogenerates. 
		print("")
		print("   and where TESTID is the id of the new test which should consist of letters, numbers and underscores, ")
		print("   for example: MyApp_perf_001 (numeric style) or InvalidFooBarProducesError ('test that XXX' long string style).")


	def printUsage(self):
		""" Print help info and exit. """
		#######                                                                                                                        |
		print("\nPySys System Test Framework (version %s): Makes PySys tests (and other assets) using configurable templates" % __version__) 
		self.printOptions()
		
		templates = self.getTemplates()
		if templates:
			print("")
			print("Available templates - and what they produce:")
			maxLength = max(len(t['name']) for t in templates)
			for t in templates:
				print(f"   {t['name']:<{maxLength}} - {t['description']}")
		
		sys.exit()

	def parseArg(self, option, value):
		if option in ['-t', '--template']:
			self.template = value
			return True
		return False

	def parseArgs(self, args):
		""" Parse the command line arguments after ``pysys make``. 
		"""
		try:
			optlist, arguments = getopt.gnu_getopt(args, self.supportedArgs[0], self.supportedArgs[1])
		except Exception:
			sys.stderr.write("Error parsing command line arguments: %s\n" % (sys.exc_info()[1]))
			sys.stderr.flush()
			self.printUsage()
			
		self.template = None
		self.testId = None

		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif not self.parseArg(option, value):
				sys.stderr.write("Unknown option: %s\n"%option)
				sys.exit(1)


		if arguments == []:
			print("A valid string test id must be supplied")
			self.printUsage(1)
		else:
			self.testId = arguments[-1]

		return self.testId

	def copy(self, source, dest): 
		"""
		Copies the specified source file/dir to the specified dest file/dir. 
		
		Can be overridden if any advanced post-processing is required. 
		"""
		if os.path.isdir(source):
			shutil.copytree(source, dest)
		else:
			shutil.copy2(source, dest)

	def makeTest(self):
		"""
		Uses the previously parsed arguments to create a new test (or related asset) on disk. 
		
		Can be overridden if additional post-processing steps are required for some templates. 
		"""
		templates = self.getTemplates()
		if self.template:
			tmp = [t for t in templates if t['name'] == self.template]
			if len(tmp) != 1: 
				raise UserError('Cannot find a template named "%s"; available templates for this project and directory are: %s'%(self.template, ', '.join(t['name'] for t in templates)))
			tmp = tmp[0]
		else:
			tmp = templates[0] # pick the default
		
		log.debug('Using template: \n%s', json.dumps(tmp, indent='  '))
		dest = self.testId
		print("Creating %s using template %s ..." % (dest, tmp['name']))
		# TODO: make sure we don't overwrite existing pysysdirconfig.xml etc
		assert tmp['isTest'] # not implemented for other asset types yet
		
		if os.path.exists(dest): raise UserError('Cannot create %s as it already exists'%dest)

		# TODO: implement replace (for files but not dirs)
		mkdir(dest)
		for d in tmp['mkdir']:	
			mkdir(dest+os.sep+d)
		for c in tmp['copy']:
			target = dest+os.sep+os.path.basename(c)
			if os.path.exists(target):
				raise Exception('Cannot copy to %s as it already exists'%target)
			self.copy(c, target)
			print("  Created %s"%target)
		
		return dest

class LegacyConsoleMakeTestHelper(object):
	"""
	The legacy and deprecated implementation of ``pysys.py make`` - used only by existing custom subclasses.
	
	Also known by its alias ``ConsoleMakeTestHelper``. 
	"""

	TEST_TEMPLATE = '''import pysys
%s
%s

class %s(%s):
	def execute(self):
		pass

	def validate(self):
		pass
	''' # not public API, do not use

	DESCRIPTOR_TEMPLATE ='''<?xml version="1.0" encoding="utf-8"?>
<pysystest type="%s">
	
	<description>
		<title></title>
		<purpose><![CDATA[
		
		]]></purpose>
	</description>

	<!-- uncomment this to skip the test:
	<skipped reason=""/> 
	-->
	
	<classification>
		<groups inherit="true">
			<group>%s</group>
		</groups>
		<modes inherit="true">
		</modes>
	</classification>

	<data>
		<class name="%s" module="%s"/>
	</data>
	
	<traceability>
		<requirements>
			<requirement id=""/>		 
		</requirements>
	</traceability>
</pysystest>
''' # deprecated, only used by legacy subclassers of this class

	def __init__(self, name=""):
		self.name = name
		self.testId = None
		self.type = "auto"
		self.testdir = os.getcwd()


	def printUsage(self):
		""" Print help info and exit. """
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		#######                                                                                                                        |
		print("\nPySys System Test Framework (version %s): New test maker" % __version__) 
		print("\nUsage: %s %s [option]+ TESTID" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -d | --dir      STRING      parent directory in which to create TESTID (default is current working dir)")
		print("       -a | --type     STRING      set the test type (auto or manual, default is auto)")
		print("       -h | --help                 print this message")
		print("")
		print("   and where TESTID is the id of the new test which should consist of letters, numbers and underscores, ")
		print("   for example: MyApp_perf_001 (numeric style) or InvalidFooBarProducesError ('test that XXX' long string style).")
		sys.exit()


	def parseArgs(self, args):
		""" Parse the command line arguments after ``pysys make``. 
		"""
		try:
			optlist, arguments = getopt.gnu_getopt(args, 'ha:d:', ["help","type=","dir="] )
		except Exception:
			print("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			self.printUsage()
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warning("Unsupported test type - valid types are auto and manual")
					sys.exit(1)	

			elif option in ("-d", "--dir"):
				self.testdir = value		

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)


		if arguments == []:
			print("A valid string test id must be supplied")
			self.printUsage()
		else:
			self.testId = arguments[0]

		return self.testId


	def makeTest(self, input=None, output=None, reference=None, descriptor=None, testclass=None, module=None,
				 group="", constantsImport=None, basetestImport=None, basetest=None, teststring=None):
		"""
		Makes a new test on disk. 
		"""
		if input==None: input = DEFAULT_INPUT
		if output==None: output = DEFAULT_OUTPUT
		if reference==None: reference = DEFAULT_REFERENCE
		if descriptor==None: descriptor = DEFAULT_DESCRIPTOR[0]
		if testclass==None: testclass = DEFAULT_TESTCLASS
		if module==None: module = DEFAULT_MODULE
		if constantsImport ==None: constantsImport = "from pysys.constants import *"
		if basetestImport == None: basetestImport = "from pysys.basetest import BaseTest"
		if basetest == None: basetest = "BaseTest"

		log.info("Creating testcase %s ..." % self.testId)
		try:	
			os.makedirs(os.path.join(self.testdir, self.testId))
			log.info("Created directory %s" % os.path.join(self.testdir, self.testId))
		except OSError:
			log.info("Error creating testcase " + os.path.join(self.testdir, self.testId) +  " - directory already exists")
			return
		else:
			os.makedirs(os.path.join(self.testdir, self.testId, input))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, input))
			os.makedirs(os.path.join(self.testdir, self.testId, output))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, output))
			os.makedirs(os.path.join(self.testdir, self.testId, reference))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, reference))
			with openfile(os.path.join(self.testdir, self.testId, descriptor), "w", encoding='utf-8') as descriptor_fp:
				descriptor_fp.write(self.DESCRIPTOR_TEMPLATE %(self.type, group, testclass, module))
			log.info("Created descriptor %s " % os.path.join(self.testdir, self.testId, descriptor))
			if not module.endswith('.py'): module += '.py'
			testclass_fp = openfile(os.path.join(self.testdir, self.testId, module), "w")
			if teststring == None:
				testclass_fp.write(self.TEST_TEMPLATE % (constantsImport, basetestImport, testclass, basetest))
			else:
				testclass_fp.write(teststring)
			testclass_fp.close()
			log.info("Created test class module %s " % os.path.join(self.testdir, self.testId, module))	

ConsoleMakeTestHelper = LegacyConsoleMakeTestHelper


def makeTest(args):
	Project.findAndLoadProject()

	cls = Project.getInstance().makerClassname.split('.')
	module = importlib.import_module('.'.join(cls[:-1]))
	maker = getattr(module, cls[-1])("make")

	try:
		maker.parseArgs(args)
		maker.makeTest()
	except UserError as e:
		sys.stdout.flush()
		sys.stderr.write("ERROR: %s\n" % e)
		sys.exit(10)

