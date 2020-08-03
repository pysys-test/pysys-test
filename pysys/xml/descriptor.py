#!/usr/bin/env pytho
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
The `TestDescriptor <pysys.xml.descriptor.TestDescriptor>` class holds metadata for each testcase 
(``pysystest.xml``) or directory (``pysysdirconfig.xml``), and the `DescriptorLoader <pysys.xml.descriptor.DescriptorLoader>` 
class allows customization of the test discovery process. 
"""

from __future__ import print_function
import os.path, logging, xml.dom.minidom
import collections
import copy
import locale

import pysys
from pysys.constants import *
from pysys.exceptions import UserError
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2, isstring, openfile

log = logging.getLogger('pysys.xml.descriptor')

class TestDescriptor(object):
	"""Descriptor metadata for an individual testcase (``pysystest.xml``) or defaults for tests under a directory 
	subtree (``pysysdirconfig.xml``). 
	
	The `DescriptorLoader` class is responsible for determining the available 
	descriptor instances. 
	
	:ivar str ~.file: The absolute path of the testcase descriptor file. 
	
	:ivar str ~.testDir: The absolute path of the test, which is used to convert 
		any relative paths into absolute paths. 
	
	:ivar str ~.id: The testcase identifier, or the id prefix if this is a 
		directory config descriptor rather than a testcase descriptor. 
		Includes a mode suffix if this is a multi-mode test and 
		supportMultipleModesPerRun=True.
	
	:ivar str ~.idWithoutMode: The raw testcase identifier with no mode suffix. 
	
	:ivar str ~.type: The kind of test this is (``auto`` or ``manual``)
	
	:ivar str ~.skippedReason: If set to a non-empty string, indicates that this 
		testcase is skipped and provides the reason. If this is set then the test 
		is skipped regardless of the value of `state`. 

	:ivar str ~.state: The state of the testcase (runnable, deprecated or skipped). This field is deprecated - we 
		recommend using `skippedReason` instead, which provides a descriptive outcome to explain why. 
		
	:ivar str ~.title: The one-line title summarizing this testcase.
	
	:ivar str ~.purpose: A detailed description of the purpose of the testcase.
	
	:ivar list[str] ~.groups: A list of the user defined groups the testcase belongs to.
	
	:ivar list[str] ~.modes: A list of the user defined modes the testcase can be run in.
	
	:ivar str ~.primaryMode: Specifies the primary mode for this test id (which may be None 
		if this test has no modes). Usually this is the first mode in the list. 
	
	:ivar str ~.mode: Specifies which of the possible modes this descriptor represents or None if the 
		the descriptor has no modes. This field is only present after the 
		raw descriptors have been expanded into multiple mode-specific 
		descriptors, and only if supportMultipleModesPerRun=True. 
		Note that after a descriptor is created from the on-disk file, the `mode` attribute is not set until 
		the later phase when multi-mode descripors are cloned and expanded based on the selected modes. 
	
	:ivar str ~.classname: The Python classname to be executed for this testcase.
	
	:ivar str ~.module: The path to the python module containing the testcase class. Relative to testDir, or an absoute path.
	
	:ivar str ~.input: The path to the input directory of the testcase. Relative to testDir, or an absoute path.
	
	:ivar str ~.output: The path to the output parent directory of the testcase. Relative to testDir, or an absoute path.
	
	:ivar str ~.reference: The path to the reference directory of the testcase. Relative to testDir, or an absoute path.
	
	:ivar list ~.traceability: A list of the requirements covered by the testcase.
	
	:ivar float ~.executionOrderHint: A float priority value used to determine the 
		order in which testcases will be run; higher values are executed before 
		low values. The default is 0.0. 
	
	:ivar bool ~.isDirConfig: True if this is a directory configuration, or False if 
		it's a normal testcase. 
	
	:ivar dict(str,obj) ~.userData: A dictionary that can be used for storing user-defined data 
		in the descriptor. In a pysystest.xml, this can be populated by one or more ``user-data`` elements e.g. 
		``<data><user-data name="key" value="val"</user-data></data>``.
	"""

	__slots__ = 'isDirConfig', 'file', 'testDir', 'id', 'type', 'state', 'title', 'purpose', 'groups', 'modes', 'mode', \
		'classname', 'module', 'input', 'output', 'reference', 'traceability', 'executionOrderHint', 'executionOrderHintsByMode', \
		'skippedReason', 'primaryMode', 'idWithoutMode', '_defaultSortKey', 'userData'

	def __init__(self, file, id, 
		type="auto", state="runnable", title=u'(no title)', purpose=u'', groups=[], modes=[], 
		classname=DEFAULT_TESTCLASS, module=DEFAULT_MODULE, 
		input=DEFAULT_INPUT, output=DEFAULT_OUTPUT, reference=DEFAULT_REFERENCE, 
		traceability=[], executionOrderHint=0.0, skippedReason=None, 
		testDir=None, 
		isDirConfig=False, userData=None):
		if skippedReason: state = 'skipped'
		if state=='skipped' and not skippedReason: skippedReason = '<unknown skipped reason>'
		self.isDirConfig = isDirConfig
		self.file = file
		if not isDirConfig:
			assert file, [file, id]
			self.testDir = testDir or os.path.dirname(file)
		self.id = id
		self.type = type
		self.state = state
		self.title = title
		self.purpose = purpose
		# copy groups/modes so we can safely mutate them later if desired
		self.groups = list(groups)
		self.modes = list(modes)
		self.classname = classname
		self.module = module
		
		self.input = input
		self.output = output
		self.reference = reference

		self.traceability = traceability
		self.executionOrderHint = executionOrderHint
		self.skippedReason = skippedReason
		
		self.primaryMode = None if not self.modes else self.modes[0]
		self.idWithoutMode = self.id
		
		# for internal use only (we cache this to speed up sorting based on path), 
		# and only for tests not dir configs; 
		# convert to lowercase to ensure a canonical sort order on case insensitive OSes; 
		# add id to be sure they're unique (e.g. including mode)
		if self.file: self._defaultSortKey = self.file.lower()+'/'+self.id
		
		# NB: self.mode is set after construction and 
		# cloning for each supported mode when supportMultipleModesPerRun=true
		
		self.userData = collections.OrderedDict() if userData is None else userData
	
	def _createDescriptorForMode(self, mode):
		"""
		Internal API for creating a test descriptor for a specific mode of this test.
		:meta private:
		"""
		assert mode, 'Mode must be specified'
		assert not hasattr(self, 'mode'), 'Cannot create a mode descriptor from a descriptor that already has its mode set'
		newdescr = copy.deepcopy(self)
		newdescr.mode = mode
		newdescr.id = self.id+'~'+mode
		newdescr._defaultSortKey = self._defaultSortKey+'~'+mode
		return newdescr
	
	def toDict(self):
		"""Converts this descriptor to an (ordered) dict suitable for serialization."""
		d = collections.OrderedDict()
		d['id'] = self.id
		d['testDir'] = self.testDir
		d['xmlDescriptor'] = self.file
		d['type'] = self.type
		d['state'] = self.state
		d['skippedReason'] = self.skippedReason
		d['title'] = self.title
		d['purpose'] = self.purpose
		d['groups'] = self.groups
		d['modes'] = self.modes
		d['primaryMode'] = self.primaryMode
		if hasattr(self, 'mode'): d['mode'] = self.mode # only if supportMultipleModesPerRun=true
		d['requirements'] = self.traceability
		
		# this is always a list with at least one item, or more if there are multiple modes
		d['executionOrderHint'] = (self.executionOrderHintsByMode
			if hasattr(self, 'executionOrderHintsByMode') else [self.executionOrderHint])

		d['classname'] = self.classname
		d['module'] = self.module
		d['input'] = self.input
		d['output'] = self.output
		d['reference'] = self.reference
		d['userData'] = self.userData
		
		return d
		
	def __str__(self):
		"""Return an informal string representation of the xml descriptor container object
		
		:return: The string represention
		:rtype: string
		"""
		
		str=    "Test id:           %s\n" % self.id
		reltestdir = self.testDir if not self.isDirConfig else '' # relative to current dir is most useful
		if reltestdir.lower().replace('\\','/').startswith(os.getcwd().lower().replace('\\','/')): reltestdir = reltestdir[len(os.getcwd())+1:]
		str=str+"Test directory:    %s\n" % reltestdir # use OS slashes to facilitate copy+paste
		str=str+"Test type:         %s\n" % self.type
		str=str+"Test state:        %s\n" % self.state
		if self.skippedReason: str=str+"Test skip reason:  %s\n" % self.skippedReason
		str=str+"Test title:        %s\n" % self.title
		str=str+"Test purpose:      "
		purpose = self.purpose.split('\n') if self.purpose is not None else ['']
		for index in range(0, len(purpose)):
			if index == 0: str=str+"%s\n" % purpose[index]
			if index != 0: str=str+"                   %s\n" % purpose[index] 

		str=str+"Test order hint:   %s\n" % (
			u', '.join('%s'%hint for hint in self.executionOrderHintsByMode) # for multi-mode tests
			if hasattr(self, 'executionOrderHintsByMode') else self.executionOrderHint)	

		str=str+"Test groups:       %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.groups) or u'<none>')
		if getattr(self, 'mode',None): # multi mode per run
			str=str+"Test mode:         %s\n" % self.mode
		else: # print available modes instead
			str=str+"Test modes:        %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.modes) or u'<none>')
		str=str+"Test classname:    %s\n" % self.classname
		str=str+"Test module:       %s\n" % self.module
		str=str+"Test input:        %s\n" % self.input
		str=str+"Test output:       %s\n" % self.output
		str=str+"Test reference:    %s\n" % self.reference
		str=str+"Test traceability: %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.traceability) or u'<none>')
		if self.userData:
			str=str+"Test user data:    %s\n" % ', '.join('%s=%s'%(k,repr(v).lstrip('u') if isstring(v) else str(v)) for k,v in (self.userData.items()))
		str=str+""
		return str
	
	def __repr__(self): return str(self)

class _XMLDescriptorCreator(object):
	'''Helper class to create a test descriptor template. DEPRECATED. 
	
	:meta private: If we want an API for this, having a writeToFile method on TestDescriptor would be a better way 
	  to go.
	'''
		
	def __init__(self, file, type="auto", group=DEFAULT_GROUP, testclass=DEFAULT_TESTCLASS, module=DEFAULT_MODULE):
		'''Class constructor.'''
		self.file=file
		self.type = type
		self.group = group
		self.testclass = testclass
		self.module = module
	
	def writeXML(self):
		'''Write a test descriptor template to file.'''
		fp = openfile(self.file, 'w')
		fp.writelines(DESCRIPTOR_TEMPLATE % (self.type, self.group, self.testclass, self.module))
		fp.close
		
XMLDescriptorContainer = TestDescriptor
""" XMLDescriptorContainer is an alias for the TestDescriptor class, which 
exists for compatibility reasons only. 

:meta private:
"""

class _XMLDescriptorParser(object):
	'''DEPRECATED - use L{DescriptorLoader.parseTestDescriptor} instead. 
	
	:meta private:
	
	Helper class to parse an XML test descriptor - either for a testcase, 
	or for defaults for a (sub-)directory of testcases.

	The class uses the minidom DOM (Document Object Model) non validating
	parser to provide accessor methods to return element attributes	and character
	data from the test descriptor file. The class is instantiated with the filename
	of the test descriptor. It is the responsibility of the user of the class to
	call the unlink() method of the class on completion in order to free the memory
	used in the parsing.
	
	'''

	def __init__(self, xmlfile, istest=True, parentDirDefaults=None, project=None):
		assert project
		self.file = xmlfile
		self.dirname = os.path.dirname(xmlfile)
		self.istest = istest
		self.defaults = self.DEFAULT_DESCRIPTOR if parentDirDefaults is None else parentDirDefaults
		roottag = 'pysystest' if istest else 'pysysdirconfig'
		if not os.path.exists(xmlfile):
			raise UserError("Unable to find supplied descriptor \"%s\"" % xmlfile)
		self.project = project
		
		try:
			self.doc = xml.dom.minidom.parse(xmlfile)
		except Exception as ex:
			raise UserError("Invalid XML in descriptor '%s': %s" % (xmlfile, ex))
		else:
			if self.doc.getElementsByTagName(roottag) == []:
				raise UserError("No <%s> element supplied in XML descriptor '%s'"%(roottag, xmlfile))
			else:
				self.root = self.doc.getElementsByTagName(roottag)[0]

	@staticmethod
	def parse(xmlfile, istest=True, parentDirDefaults=None, project=None):
		"""
		Parses the test/dir descriptor in the specified path and returns the 
		TestDescriptor object. 
		
		:param istest: True if this is a pysystest.xml file, false if it is 
			a descritor giving defaults for a directory of testcases.  
			:param parentDirDefaults: Optional TestDescriptor instance 
			specifying default values to be filtered in from the parent 
			directory.
		"""
		p = _XMLDescriptorParser(xmlfile, istest=istest, parentDirDefaults=parentDirDefaults, project=project)
		try:
			return p.getContainer()
		finally:
			p.unlink()

	DEFAULT_DESCRIPTOR = TestDescriptor(
		file=None, id=u'', type="auto", state="runnable", 
		title='', purpose='', groups=[], modes=[], 
		classname=DEFAULT_TESTCLASS, module=DEFAULT_MODULE,
		input=DEFAULT_INPUT, output=DEFAULT_OUTPUT, reference=DEFAULT_REFERENCE, 
		traceability=[], executionOrderHint=0.0, skippedReason=None, isDirConfig=True)
	"""
	A directory config descriptor instance of TestDescriptor holding 
	the default values to be used if there is no directory config descriptor. 
	"""


	def getContainer(self):
		'''Create and return an instance of TestDescriptor for the contents of the descriptor.'''
		
		for attrName, attrValue in self.root.attributes.items():
			if attrName not in ['state', 'type']:
				raise UserError('Unknown attribute "%s" in XML descriptor "%s"'%(attrName, self.file))
		
		# some elements that are mandatory for an individual test and not used for dir config
		return TestDescriptor(self.getFile(), self.getID(), self.getType(), self.getState(),
										self.getTitle() if self.istest else '', self.getPurpose() if self.istest else '',
										self.getGroups(), self.getModes(),
										self.project.expandProperties(self.getClassDetails()[0]),
										self.project.expandProperties(self.getClassDetails()[1]),
										self.getTestInput(),
										self.getTestOutput(),
										self.getTestReference(),
										self.getRequirements(), 
										self.getExecutionOrderHint(), 
										skippedReason=self.getSkippedReason(), 
										testDir=self.dirname,
										userData=self.getUserData(),
										isDirConfig=not self.istest)


	def unlink(self):
		'''Clean up the DOM on completion.'''
		if self.doc: self.doc.unlink()

	
	def getFile(self):
		'''Return the filename of the test descriptor.'''
		return self.file

	
	def getID(self):
		'''Return the id of the test, or for a pysysdirconfig, the id prefix.'''
		id = self.defaults.id
		for e in self.root.getElementsByTagName('id-prefix'):
			id = id+self.getText(e)
		
		for c in u'\\/:~#<>':
			# reserve a few characters that we might need for other purposes; _ and . can be used however
			if c in id:
				raise UserError('The <id-prefix> is not permitted to contain "%s"; error in "%s"'%(c, self.file))
		
		if self.istest: id = id+os.path.basename(self.dirname)
		
		return id


	def getType(self):
		'''Return the type attribute of the test element.'''
		type = self.root.getAttribute("type") or self.defaults.type
		if type not in ["auto", "manual"]:
			raise UserError("The type attribute of the test element should be \"auto\" or \"manual\" in \"%s\""%self.file)
		return type


	def getState(self):
		'''Return the state attribute of the test element.'''
		state = self.root.getAttribute("state")	 or self.defaults.state
		if state not in ["runnable", "deprecated", "skipped"]: 
			raise UserError("The state attribute of the test element should be \"runnable\", \"deprecated\" or \"skipped\" in \"%s\""%self.file)
		return state 

	def getSkippedReason(self):
		for e in self.root.getElementsByTagName('skipped'):
			r = (e.getAttribute('reason') or '').strip() 
			# make this mandatory, to encourage good practice
			if not r: raise UserError('Missing reason= attribute in <skipped> element of "%s"'%self.file)
			return r
		return self.defaults.skippedReason

	def getTitle(self):
		'''Return the test titlecharacter data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise UserError("No <description> element supplied in XML descriptor \"%s\""%self.file)
		
		if descriptionNodeList[0].getElementsByTagName('title') == []:
			raise UserError("No <title> child element of <description> supplied in XML descriptor \"%s\""%self.file)
		else:
			try:
				title = descriptionNodeList[0].getElementsByTagName('title')[0]
				return title.childNodes[0].data.strip()
			except Exception:
				return self.defaults.title
				
				
	def getPurpose(self):
		'''Return the test purpose character data of the description element.'''
		descriptionNodeList = self.root.getElementsByTagName('description')
		if descriptionNodeList == []:
			raise UserError("No <description> element supplied in XML descriptor \"%s\""%self.file)
		
		if descriptionNodeList[0].getElementsByTagName('purpose') == []:
			raise UserError("No <purpose> child element of <description> supplied in XML descriptor \"%s\""%self.file)
		else:
			try:
				purpose = descriptionNodeList[0].getElementsByTagName('purpose')[0]
				return purpose.childNodes[0].data.strip()
			except Exception:
				return self.defaults.purpose
			
				
	def getGroups(self):
		'''Return a list of the group names, contained in the character data of the group elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		groupList = []
		try:
			groups = classificationNodeList[0].getElementsByTagName('groups')[0]
			for node in groups.getElementsByTagName('group'):
				if self.getText(node): groupList.append(self.getText(node))

			if (groups.getAttribute('inherit') or 'true').lower()!='true':
				return groupList
		except Exception:
			pass
			
		groupList = [x for x in self.defaults.groups if x not in groupList]+groupList
		return groupList
	
				
	def getModes(self):
		'''Return a list of the mode names, contained in the character data of the mode elements.'''
		classificationNodeList = self.root.getElementsByTagName('classification')
		
		modeList = []
		try:
			modes = classificationNodeList[0].getElementsByTagName('modes')[0]
			for node in modes.getElementsByTagName('mode'):
				if self.getText(node): modeList.append(self.getText(node))

			if (modes.getAttribute('inherit') or 'true').lower()!='true':
				return modeList

		except Exception:
			pass
		modeList = [x for x in self.defaults.modes if x not in modeList]+modeList
		return modeList

				
	def getClassDetails(self):
		'''Return the test class attributes (name, module, searchpath), contained in the class element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			el = dataNodeList[0].getElementsByTagName('class')[0]
			return [el.getAttribute('name'), el.getAttribute('module')]
		except Exception:
			return [self.defaults.classname, self.defaults.module]

	def getExecutionOrderHint(self):
		r = None
		for e in self.root.getElementsByTagName('execution-order'):
			r = e.getAttribute('hint')
			if r:
				try:
					r = float(r)
				except Exception:
					raise UserError('Invalid float value specified for execution-order hint in "%s"'%self.file)
		if r is None or r == '': 
			return self.defaults.executionOrderHint
		else:
			return r
			
	def getTestInput(self):
		'''Return the test input path, contained in the input element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			input = dataNodeList[0].getElementsByTagName('input')[0]
			return input.getAttribute('path')
		except Exception:
			return self.defaults.input

	def getUserData(self):
		'''Return the userData from the user-data element.'''
		# start with parent defaults, add children
		result = collections.OrderedDict(self.defaults.userData)
		for data in self.root.getElementsByTagName('data'):
			for e in data.getElementsByTagName('user-data'):
				key = e.getAttribute('name').strip()
				assert key, 'name= must be specified'
				assert key not in {'input', 'output', 'reference', 'descriptor', 'runner', 'log', 'project', 'lock'}, key # prevent names that we reserve for use by the basetest/processuser
				result[key] = e.getAttribute('value')
		return result

	def getTestOutput(self):
		'''Return the test output path, contained in the output element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			output = dataNodeList[0].getElementsByTagName('output')[0]
			return output.getAttribute('path')
		except Exception:
			return self.defaults.output


	def getTestReference(self):
		'''Return the test reference path, contained in the reference element.'''
		try:
			dataNodeList = self.root.getElementsByTagName('data')
			ref = dataNodeList[0].getElementsByTagName('reference')[0]
			return ref.getAttribute('path')
		except Exception:
			return self.defaults.reference


	def getRequirements(self):
		'''Return a list of the requirement ids, contained in the character data of the requirement elements.'''
		reqList = []			
		try:
			traceabilityNodeList = self.root.getElementsByTagName('traceability')
			requirements = traceabilityNodeList[0].getElementsByTagName('requirements')[0]
			for node in requirements.getElementsByTagName('requirement'):
				if node.getAttribute('id'): reqList.append(node.getAttribute('id'))
		except Exception:
			pass
		reqList = [x for x in self.defaults.traceability if x not in reqList]+reqList
		return reqList

	@staticmethod
	def getText(element):
		"""Utility method that reads text from the specified element and 
		strips leading/trailing whitespace from it. Returns an empty string if none. """
		t = u''
		if not element: return t
		for n in element.childNodes:
			if (n.nodeType == element.TEXT_NODE) and n.data:
				t += n.data
		return t.strip()


class DescriptorLoader(object):
	"""
	This class is responsible for locating and loading all available testcase 
	descriptors. 
	
	A custom DescriptorLoader subclass can be provided to customize the test 
	discovery process, typically by overriding L{loadDescriptors} and modifying the 
	returned list of descriptors and configuring your ``pysysproject.xml`` with::
	
		<descriptor-loader module="mypkg.custom" classname="CustomDescriptorLoader"/>
	
	You could use this approach to add additional descriptor instances 
	to represent non-PySys testcases found under the search directory, for example 
	based on discovery of unit test classes. 
	
	Another key use case would be dynamically adding or changing descriptor 
	settings such as the list of modes for each testcase or the 
	executionOrderHint, perhaps based on a per-group basis. For example, 
	you could modify descriptors in the "database-tests" group to have a 
	dynamically generated list of modes identifying the possible database 
	servers supported without having to hardcode that list into any descriptor 
	files on disk, and allowing for different database modes on different 
	platforms. 

	:ivar pysys.xml.project.Project ~.project: The `pysys.xml.project.Project` instance. 
	
	"""
	def __init__(self, project, **kwargs): 
		assert project, 'project must be specified'
		self.project = project
		
		self.__descriptorLoaderPlugins = []
		for (pluginCls, pluginProperties) in project._descriptorLoaderPlugins:
			plugin = pluginCls()
			plugin.project = project
			pysys.utils.misc.setInstanceVariablesFromDict(plugin, pluginProperties, errorOnMissingVariables=True)
			plugin.setup(project)
			self.__descriptorLoaderPlugins.append(plugin)

	def loadDescriptors(self, dir, **kwargs):
		"""Find all descriptors located under the specified directory, and 
		return them as a list.
		
		Subclasses may change the returned descriptors and/or add additional 
		instances of their own to the list after calling the super implementation::
		
		  descriptors = super(CustomDescriptorLoader, self).loadDescriptors(dir, **kwargs)
		  ...
		  return descriptors
		
		:param dir: The parent directory to search for runnable tests. 
		
		:return: List of L{pysys.xml.descriptor.TestDescriptor} objects 
			which could be selected for execution. 
			
			If a test can be run in multiple modes there must be a single descriptor 
			for it in the list returned from this method. Each multi-mode 
			descriptor is later expanded out into separate mode-specific 
			descriptors (at the same time as descriptor filtering based on 
			command line arguments, and addition of project-level 
			execution-order), before the final list is sorted and passed to 
			L{pysys.baserunner.BaseRunner}. 
			
			The order of the returned list is random, so the caller is responsible 
			for sorting this list to ensure deterministic behaviour. 
		
		:rtype: list
		:raises UserError: Raised if no testcases can be found.
		
		"""
		assert not kwargs, 'reserved for future use: %s'%kwargs.keys()
		assert self.project, 'project must be specified'
		assert dir, 'dir must be specified'
		assert os.path.isabs(dir), 'dir must be an absolute path: %s'%dir
		
		project = self.project
		
		descriptors = []
		ignoreSet = set(OSWALK_IGNORES)
		
		descriptorSet = set([s.strip() for s in project.getProperty('pysysTestDescriptorFileNames', default=','.join(DEFAULT_DESCRIPTOR)).split(',')])
		
		assert project.projectFile != None
		log = logging.getLogger('pysys.launcher')

		# although it's highly unlikely, if any test paths did slip outside the Windows 256 char limit, 
		# it would be very dangerous to skip them (which is what os.walk does unless passed a \\?\ path), 
		# so must use long-path-safe - but need to re-encode from unicode string back to bytestring in Python 2
		i18n_reencode = locale.getpreferredencoding() if PY2 and isinstance(dir, str) else None
		
		dir = toLongPathSafe(os.path.normpath(dir))
		assert os.path.exists(dir), dir # sanity check
		if project.projectFile:
			projectroot = toLongPathSafe(os.path.normpath(os.path.dirname(project.projectFile)))

		DIR_CONFIG_DESCRIPTOR = 'pysysdirconfig.xml'
		if not project.projectFile or not dir.startswith(projectroot):
			dirconfigs = None
			log.debug('Project file does not exist under "%s" so processing of %s files is disabled', dir, DIR_CONFIG_DESCRIPTOR)
		else:
			# find directory config descriptors between the project root and the testcase 
			# dirs. We deliberately use project dir not current working dir since 
			# we don't want descriptors to be loaded differently depending on where the 
			# tests are run from (i.e. should be independent of cwd). 
			dirconfigs = {}

			# load any descriptors between the project dir up to (but not including) the dir we'll be walking
			searchdirsuffix = dir[len(projectroot)+1:].split(os.sep) if len(dir)>len(projectroot) else []
			currentconfig = None
			for i in range(len(searchdirsuffix)): # up to but not including dir
				if i == 0:
					currentdir = projectroot
				else:
					currentdir = projectroot+os.sep+os.sep.join(searchdirsuffix[:i])
				
				if pathexists(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR):
					currentconfig = self._parseTestDescriptor(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR, parentDirDefaults=currentconfig, isDirConfig=True)
					log.debug('Loaded directory configuration descriptor from %s: \n%s', currentdir, currentconfig)
			# this is the top-level directory that will be checked below
			dirconfigs[os.path.dirname(dir)] = currentconfig

		for root, dirs, files in os.walk(toLongPathSafe(dir)):
			ignorematch = next( (f for f in files if (f == '.pysysignore' or f == 'pysysignore')), None)
			if ignorematch:
				log.debug('Skipping directory %s due to ignore file %s', root, ignorematch)
				del dirs[:]
				continue
				
			parentconfig = None
			if dirconfigs is not None:
				parentconfig = dirconfigs[os.path.dirname(root)]
				if next( (f for f in files if (f == DIR_CONFIG_DESCRIPTOR)), None):
					parentconfig = self._parseTestDescriptor(root+os.sep+DIR_CONFIG_DESCRIPTOR, parentDirDefaults=parentconfig, isDirConfig=True)
					log.debug('Loaded directory configuration descriptor from %s: \n%s', root, parentconfig)

			# allow subclasses to modify descriptors list and/or avoid processing 
			# subdirectories
			if self._handleSubDirectory(root, dirs, files, descriptors, parentDirDefaults=parentconfig):
				del dirs[:]
				continue

			intersection = descriptorSet & set(files)
			if intersection: 
				descriptorfile = fromLongPathSafe(os.path.join(root, intersection.pop()))
				# PY2 gets messed up if we start passing unicode rather than byte str objects here, 
				# as it proliferates to all strings in each test
				if i18n_reencode is not None: descriptorfile = descriptorfile.encode(i18n_reencode) 

				try:
					parsed = self._parseTestDescriptor(descriptorfile, parentDirDefaults=parentconfig)
					if parsed:
						descriptors.append(parsed)
				except UserError:
					raise # no stack trace needed, will already include descriptorfile name
				except Exception as e:
					log.info('Failed to read descriptor: ', exc_info=True)
					raise Exception("Error reading descriptor file '%s': %s - %s" % (descriptorfile, e.__class__.__name__, e))

				# if this is a test dir, it never makes sense to look at sub directories
				del dirs[:]
				continue
			
			for ignore in (ignoreSet & set(dirs)): dirs.remove(ignore)

			if dirconfigs is not None and len(dirs)>0:
				# stash it for when we navigate down to subdirectories
				# only add to dict if we're continuing to process children
				dirconfigs[root] = parentconfig 

		return descriptors
		
	def _handleSubDirectory(self, dir, subdirs, files, descriptors, parentDirDefaults, **kwargs):
		"""Overrides the handling of each sub-directory found while walking 
		the directory tree during `loadDescriptors`. 
		
		Can be used to add test descriptors, and/or add custom logic for 
		preventing PySys searching a particular part of the directory tree 
		perhaps based on the presence of specific files or subdirectories 
		within it. 

		This method is called before directories containing pysysignore 
		files are stripped out. 
		
		:param str dir: The full path of the directory to be processed.
			On Windows, this will be a long-path safe unicode string. 
		:param list[str] subdirs: a list of the subdirectories under dir, which 
			can be used to detect what kind of directory this is, and also can be modified by this method to prevent 
			other loaders looking at subdirectories. 
		:param list[str] files: a list of the files under dir, which 
			can be used to detect what kind of directory this is, and also can be modified by this method to prevent 
			other loaders looking at them. 
		:param list[TestDescriptor] descriptors: A list of `TestDescriptor` items which this method 
			can add to if desired. 
		:param TestDescriptor parentDirDefaults: A `TestDescriptor` containing defaults 
			from the parent directory, or None if there are none. Test loaders may 
			optionally merge some of this information with test-specific 
			information when creating test descriptors. 
		:param dict kwargs: Reserved for future use. Pass this to the base class 
			implementation when calling it. 
		:return: If True, this part of the directory tree has been fully 
			handled and PySys will not search under it any more. False to allow 
			normal PySys handling of the directory to proceed. 
		"""
		assert not kwargs, 'reserved for future use: %s'%kwargs.keys()
		
		# default implementation just delegates to any plugins
		for p in self.__descriptorLoaderPlugins:
			if p.addDescriptorsFromDirectory(dir=dir, subdirs=subdirs, files=files, parentDirDefaults=parentDirDefaults, descriptors=descriptors, **kwargs):
				return True
		
		return False

	def _parseTestDescriptor(self, descriptorfile, parentDirDefaults=None, isDirConfig=False, **kwargs):
		""" Parses a single descriptor file (typically an XML file) for a testcase or directory configuration 
		and returns the resulting descriptor. 
		
		:param descriptorfile: The absolute path of the descriptor file. 
		:param parentDirDefaults: A L{TestDescriptor} instance containing 
			defaults to inherit from the parent directory, or None if none was found. 
		:param isDirConfig: False for normal test descriptors, True for a directory configuration. 
		:return: The L{TestDescriptor} instance, or None if none should be 
			added for this descriptor file. Note that subclasses may modify the 
			contents of the returned instance. 
		:raises UserError: If the descriptor is invalid and an error should be 
			displayed to the user without any Python stacktrace. 
			The exception message must contain the path of the descriptorfile.
		"""
		assert not kwargs, 'reserved for future use: %s'%kwargs.keys()
		return _XMLDescriptorParser.parse(descriptorfile, parentDirDefaults=parentDirDefaults, istest=not isDirConfig, project=self.project)
