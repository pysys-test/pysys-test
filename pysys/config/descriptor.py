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
The `TestDescriptor <pysys.config.descriptor.TestDescriptor>` class holds metadata for each testcase 
(``pysystest.xml``) or directory (``pysysdirconfig.xml``), and the `DescriptorLoader <pysys.config.descriptor.DescriptorLoader>` 
class allows customization of the test discovery process. 
"""

from __future__ import print_function
import os.path, logging, xml.dom.minidom
import collections
import copy
import locale
import inspect

import pysys
from pysys.constants import *
from pysys.exceptions import UserError
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import PY2, isstring, openfile, makeReadOnlyDict

log = logging.getLogger('pysys.config.descriptor')

class TestDescriptor(object):
	"""Descriptor metadata for an individual testcase (``pysystest.xml``) or defaults for tests under a directory 
	subtree (``pysysdirconfig.xml``); see :doc:`../TestDescriptors`. 
	
	The `DescriptorLoader` class is responsible for determining the available 
	descriptor instances. 
	
	:ivar str ~.file: The absolute path of the testcase descriptor file. 
	
	:ivar str ~.testDir: The absolute path of the test, which is used to convert 
		any relative paths into absolute paths. 
	
	:ivar str ~.id: The testcase identifier, or the id prefix if this is a 
		directory config descriptor rather than a testcase descriptor. 
		Includes a mode suffix if this is a multi-mode test.
	
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
	
	:ivar list[TestMode|str] ~.modes: A list of the user defined modes the testcase can be run in. Usually these will be 
		`TestMode` instances, but older tests with custom TestLoaders may add simple strings here instead. 

	:ivar TestMode|str ~.primaryMode: Specifies the primary mode for this test id (which may be None 
		if this test has no modes). Usually this is the first mode in the list. 
	
	:ivar TestMode|str ~.mode: Specifies which of the possible modes this descriptor represents or None if the 
		the descriptor has no modes. This field is only present after the 
		raw descriptors have been expanded into multiple mode-specific descriptors. 
		Note that after a descriptor is created from the on-disk file, the `mode` attribute is not set until 
		the later phase when multi-mode descriptors are cloned and expanded based on the selected modes. 
		You can use ``descriptor.mode.params`` to get the parameter dictionary for this mode. 
	
	:ivar str ~.classname: The Python classname to be executed for this testcase.
	
	:ivar str ~.module: The path to the python module containing the testcase class. Relative to testDir, or an absolute path.
		If not set, the class is looked up in the PYTHONPATH. 
	
	:ivar str ~.input: The path to the input directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar str ~.output: The path to the output parent directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar str ~.reference: The path to the reference directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar list ~.traceability: A list of the requirements covered by the testcase, typically keywords or bug/story ids.
	
	:ivar float ~.executionOrderHint: A float priority value used to determine the 
		order in which testcases will be run; higher values are executed before 
		low values. The default is 0.0. 
	
	:ivar bool ~.isDirConfig: True if this is a directory configuration, or False if 
		it's a normal testcase. 
	
	:ivar dict[str,obj] ~.userData: A dictionary that can be used for storing user-defined data 
		in the descriptor. In a pysystest.xml, this can be populated by one or more ``user-data`` elements, e.g. 
		``<data><user-data name="key" value="val ${projectProperty}"</user-data></data>``.
	"""

	__slots__ = 'isDirConfig', 'file', 'testDir', 'id', 'type', 'state', 'title', 'purpose', 'groups', 'modes', 'mode', \
		'classname', 'module', 'input', 'output', 'reference', 'traceability', 'executionOrderHint', 'executionOrderHintsByMode', \
		'skippedReason', 'primaryMode', 'idWithoutMode', '_defaultSortKey', 'userData', '_makeTestTemplates', 

	def __init__(self, file, id, 
		type="auto", state="runnable", title=u'', purpose=u'', groups=[], modes=[], 
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
		assert classname, 'Test descriptors cannot set the classname to nothing'

		if not module: self.module = None
		elif module.endswith('.py'): self.module = module
		else: self.module = module+'.py'
		
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
		# cloning for each supported mode 
		
		self.userData = collections.OrderedDict() if userData is None else userData
	
	def _createDescriptorForMode(self, mode):
		"""
		Internal API for creating a test descriptor for a specific mode of this test.
		:meta private:
		"""
		assert mode, 'Mode must be specified'
		assert not hasattr(self, 'mode'), 'Cannot create a mode descriptor from a descriptor that already has its mode set'
		newdescr = copy.deepcopy(self) # nb: the mode can't be deep copied accurately but of course it's not set yet so no problem!
		newdescr.mode = mode # we assume the passed in mode is the TestMode object (not just a str) if TestMode is what's in the descriptor
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
		d['modeParameters'] = {str(m):m.params for m in self.modes}
		d['primaryMode'] = self.primaryMode
		if hasattr(self, 'mode'): d['mode'] = self.mode 
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
		
		s=    "Test id:           %s\n" % self.id
		reltestdir = self.testDir if not self.isDirConfig else '' # relative to current dir is most useful
		if reltestdir.lower().replace('\\','/').startswith(os.getcwd().lower().replace('\\','/')): reltestdir = reltestdir[len(os.getcwd())+1:]
		s=s+"Test directory:    %s\n" % reltestdir # use OS slashes to facilitate copy+paste
		s=s+"Test type:         %s\n" % self.type
		s=s+"Test state:        %s\n" % self.state
		if self.skippedReason: s=s+"Test skip reason:  %s\n" % self.skippedReason
		s=s+"Test title:        %s\n" % self.title
		s=s+"Test purpose:      "
		purpose = self.purpose.split('\n') if self.purpose is not None else ['']
		for index in range(0, len(purpose)):
			if index == 0: s=s+"%s\n" % purpose[index]
			if index != 0: s=s+"                   %s\n" % purpose[index] 

		s=s+"Test groups:       %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.groups) or u'<none>')
		
		longestmode = max(len(m) for m in self.modes) if self.modes else 0
		def modeToString(m):
			x = u"'%s'"%m if u' ' in m else m
			x = (u"%-"+str(longestmode+1)+"s")%x
			if getattr(m, 'params', None):
				x += u'{%s}'%', '.join(u'%s=%r'%(k,v) for (k,v) in m.params.items())
			return x.strip()
		
		if getattr(self, 'mode',None): # multi mode per run
			s=s+"Test mode:         %s\n" % modeToString(self.mode)
		else: # print available modes instead
			modeDelim = u'\n --> ' if any(getattr(m, 'params', None) for m in self.modes) else u', '
			s=s+("Test modes:        %s%s\n") % (modeDelim if '\n' in modeDelim else '', modeDelim.join(modeToString(x) for x in self.modes) or u'<none>')

		s=s+"Test order hint:   %s\n" % (
			u', '.join('%s'%hint for hint in self.executionOrderHintsByMode) # for multi-mode tests
			if hasattr(self, 'executionOrderHintsByMode') else self.executionOrderHint)	

		s=s+"Test classname:    %s\n" % self.classname
		s=s+"Test module:       %s\n" % self.module
		s=s+"Test input:        %s\n" % self.input
		s=s+"Test output:       %s\n" % self.output
		s=s+"Test reference:    %s\n" % self.reference
		s=s+"Test traceability: %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.traceability) or u'<none>')
		if self.userData:
			s=s+"Test user data:    %s\n" % ', '.join('%s=%s'%(k,self.__userDataValueToString(v)) for k,v in (self.userData.items()))
		s=s+""
		return s
	
	@staticmethod
	def __userDataValueToString(v):
		if not isstring(v): return str(v)
		if '\n' in v:
			# tab and newline character are difficult to read and in most cases whitespace will be stripped out so remove 
			# it from this view of the strings
			v = '<nl>'.join(x.strip() for x in v.split('\n') if x.strip())
		return repr(v).lstrip('u')
	
	def __repr__(self): return str(self)

XMLDescriptorContainer = TestDescriptor
""" XMLDescriptorContainer is an alias for the TestDescriptor class, which 
exists for compatibility reasons only. 

:meta private:
"""

class TestMode(str): # subclasses string to retain compatibility for tests that don't use mode parameters
	"""Represents a mode that a test can run in, and optionally a dict of parameters that define that mode. 
	
	To create one::
	
		mode = TestMode('MyMode', {'param1': 'value1'})
	
	See the ``mode`` parameter/field in `TestDescriptor` where this class is used. 
	
	This class is immutable, so create a new instance if you want to change something. 

	For convenience and compatibility, this TestMode subclasses a string holding the mode. 
	
	:ivar dict[str,obj] ~.params: A dictionary of parameters associated with this mode. The parameters are available to 
		the test (as ``self.mode.params``) and also assigned as instance fields on the test class when it 
		runs in this mode. 

	.. versionadded:: 2.0

	"""
	__slots__ = ['params']
	
	def __new__(cls,s,params=None):
		self = str.__new__(cls,s)
		self.params = params
		return self

	def __setattr__(self, attr, value):
		if attr in self.__slots__ and getattr(self, attr, None) is None: 
			object.__setattr__(self, attr, value)
		else:
			raise TypeError('Cannot modify immutable instance by setting %s'%(attr))


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

	def __init__(self, xmlfile, istest=True, parentDirDefaults=None, project=None, xmlRootElement=None):
		assert project
		self.file = xmlfile
		self.dirname = os.path.dirname(xmlfile)
		self.istest = istest
		self.defaults = (project._defaultDirConfig or self.DEFAULT_DESCRIPTOR) if parentDirDefaults is None else parentDirDefaults
		roottag = 'pysystest' if istest else 'pysysdirconfig'
		if not os.path.exists(xmlfile):
			raise UserError("Unable to find supplied descriptor \"%s\"" % xmlfile)
		self.project = project
		
		if xmlRootElement: # used when parsing from project XML rather than directly from a standalone file
			self.doc = None
			self.root = xmlRootElement
			assert xmlRootElement.tagName == 'pysysdirconfig', xmlRootElement.tagName
			return
		
		if istest and not xmlfile.endswith('.xml'):
			# Find it within a file of another type e.g. pysystest.py
			# Open in binary mode since we don't know the encoding - we'll rely on the XML header to tell us if it's anything unusual
			with open(xmlfile, 'rb') as xmlhandle:
				self.nonXMLContents = xmlhandle.read()
			match = re.search(b'(<[?]xml[^>]*>\\s*<pysystest.*>.*</pysystest>)', self.nonXMLContents, flags=re.DOTALL)
			if not match: raise UserError("No <pysystest> XML descriptor was found in file \"%s\""%(xmlfile))
			xmlcontents = match.group(0)
		else:
			xmlcontents = None
			self.nonXMLContents = None
		
		try:
			if xmlcontents:
				self.doc = xml.dom.minidom.parseString(xmlcontents)
			else:
				self.doc = xml.dom.minidom.parse(xmlfile)
		except Exception as ex:
			raise UserError("Invalid XML in descriptor '%s': %s" % (xmlfile, ex))
		else:
			if self.doc.getElementsByTagName(roottag) == []:
				raise UserError("No <%s> element supplied in XML descriptor '%s'"%(roottag, xmlfile))
			else:
				self.root = self.doc.getElementsByTagName(roottag)[0]

	@staticmethod
	def parse(xmlfile, istest=True, parentDirDefaults=None, project=None, **kwargs):
		"""
		Parses the test/dir descriptor in the specified path and returns the 
		TestDescriptor object. 
		
		:param istest: True if this is a pysystest.xml file, false if it is 
			a descritor giving defaults for a directory of testcases.  
			:param parentDirDefaults: Optional TestDescriptor instance 
			specifying default values to be filtered in from the parent 
			directory.
		"""
		p = _XMLDescriptorParser(xmlfile, istest=istest, parentDirDefaults=parentDirDefaults, project=project, **kwargs)
		try:
			return p.getContainer()
		finally:
			p.unlink()

	DEFAULT_DESCRIPTOR = TestDescriptor(
		file=None, id=u'', type="auto", state="runnable", 
		title='', purpose='', groups=[], modes=[], 
		classname=DEFAULT_TESTCLASS, module=None,
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
		cls, pymodule = self.getClassDetails()
		
		if pymodule is None and self.istest: # default setting (nb: NOT the same as pymodule='' which means to use the PYTHONPATH)
			pymodule = os.path.basename(self.file) if self.file.endswith('.py') else DEFAULT_MODULE # else run.py
		
		
		
		# some elements that are mandatory for an individual test and not used for dir config
		t = TestDescriptor(self.getFile(), self.getID(), self.getType(), self.getState(),
										self.getTitle() if self.istest else '', self.getPurpose() if self.istest else '',
										self.getGroups(), self.getModes(), 
										self.project.expandProperties(cls),
										self.project.expandProperties(pymodule),
										self.project.expandProperties(self.getTestInput()),
										self.project.expandProperties(self.getTestOutput()),
										self.project.expandProperties(self.getTestReference()),
										self.getRequirements(), 
										self.getExecutionOrderHint(), 
										skippedReason=self.getSkippedReason(), 
										testDir=self.dirname,
										userData=self.getUserData(),
										isDirConfig=not self.istest)
		
		if not self.istest:
			# _makeTestTemplates is not an official/public part of the descriptor spec, so don't have it in the constructor signature
			t._makeTestTemplates = self._parseTestMakerTemplates()
		
		return t

	def _parseTestMakerTemplates(self): # not public API, do not use
		templates = []

		for e in self.root.getElementsByTagName('maker-template'):
			t = {
				'name': e.getAttribute('name'),
				'description': e.getAttribute('description'),
				'copy':   [x for x in (e.getAttribute('copy') or '').split(',') if x.strip()],
				'mkdir': None if not e.hasAttribute('mkdir') else
					[self.project.expandProperties(x).strip() for x in (e.getAttribute('mkdir') or '').split(',') if self.project.expandProperties(x).strip()],
				'isTest': (e.getAttribute('isTest') or '').lower() != 'false',
				'replace': [],
				'source': self.file,
			}
			
			# NB: further validation and expansion happens in console_make
			
			if not t['name']: raise UserError("A name=... attribute is required for each maker-template in \"%s\""%self.file)
			if not t['description']: raise UserError("A description=... attribute is required for each maker-template, in \"%s\""%self.file)
			
			for r in e.getElementsByTagName('replace'):
				r1, r2 = r.getAttribute('regex'), r.getAttribute('with')
				if not r1 or not r2: raise UserError("Each make-test-template <replace> element requires both a regex= and a with= attribute, in \"%s\""%self.file)
				t['replace'].append( (r1, r2) )
			templates.append(t)

		# NB: we don't combine with defaults here, that happens in the make launcher

		return templates


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

	def findNonXMLTextValue(self, name):
		"""
		Attempts to read a string literal value in non-XML form using __pysystest_<name>__ syntax, 
		for example from a pysystest.py python file. This avoids messy CDATA escaping needed in XML for common characters 
		such as < and >. 
		
		Returns None if not found. 
		"""
		if self.nonXMLContents is None: return None

		# Find it within a file of another type e.g. pysystest.py
		name = '__pysystest_%s__'%name
		match = re.search(b'(^|\\n)[ \\t]*%s *= *"+([^"]+)"'%name.encode('ascii'), self.nonXMLContents, flags=re.DOTALL) # must be at the start of a line
		if not match: return None
		x = match.group(2).decode('utf-8')
		if '\\' in x: raise UserError("%s must be a simple string literal with no backslash escape sequences; cannot parse \"%s\""%(name, self.file))
		return x
		

	def getTitle(self):
		'''Return the test title character data of the description element.'''
		# PySys 1.6.1 gave an error if <description> was missing, but a default if <title> was missing, and permitted empty string. So don't be too picky. 

		result = self.getElementTextOrDefault('title', optionalParents=['description']) or self.findNonXMLTextValue('title')
		if not result and self.istest: result = self.getID() # falling back to the ID is better than nothing
		
		result = result.replace('\n',' ').replace('\r',' ').replace('\t', ' ').strip()
		if '  ' in result: result = re.sub('  +', ' ', result)
		return result

				
	def getPurpose(self):
		'''Return the test purpose character data of the description element.'''
		
		result = self.getElementTextOrDefault('purpose', optionalParents=['description']) or self.findNonXMLTextValue('purpose')
		if result is None: result = self.defaults.purpose
		
		if not result: return result
		return inspect.cleandoc(result.replace('\r','').replace('\t', '  ')).strip()

				
	def getGroups(self):
		'''Return a list of the group names, contained in the character data of the group elements.'''

		groupList = []
		groups = self.getSingleElement('groups', optionalParents=['classification'])
		if groups:
			if groups.parentNode.tagName not in ['pysystest', 'pysysdirconfig', 'classification']: 
				raise UserError("<groups> element found under <%s> but must be under the root node (or the <classification> node), in XML descriptor \"%s\""%(groups.parentNode.tagName, self.file))

			if groups.getAttribute('groups'):
				groupList.extend(g.strip() for g in groups.getAttribute('groups').split(',') if g.strip())

			for node in groups.getElementsByTagName('group'):
				g = self.getText(node)
				if g and g.strip():
					groupList.append(g.strip())

			if (groups.getAttribute('inherit') or 'true').lower()!='true':
				return groupList # don't inherit
		
		groupList = [x for x in self.defaults.groups if x not in groupList]+groupList
		return groupList
	
				
	def getModes(self):
		modesNodes = self.root.getElementsByTagName('modes')
		if not modesNodes: return self.defaults.modes # by default we inherit (unless there are multiple <modes> elements in the file)
		
		result = {} # key=mode name value=params
		for modesNode in modesNodes:
			if modesNode.parentNode.tagName not in ['pysystest', 'pysysdirconfig', 'classification']: 
				raise UserError("<modes> element found under <%s> but must be under the root node (or the <classification> node), in XML descriptor \"%s\""%(modesNode.parentNode.tagName, self.file))
			prevModesForCombining = None if not result else result

			# by default we inherit, but to avoid confusion when defining multiple mode matrices we only allow explicit inherits 
			defaultinherit = len(modesNodes) <= 1
			if (modesNode.getAttribute('inherit') or str(defaultinherit)).lower()!='true': 
				result = {}
			else:
				result = {m:m.params for m in self.defaults.modes}
			
			for node in modesNode.getElementsByTagName('mode'):
				if not node.hasAttributes():
					params = {}
				else:
					params = collections.OrderedDict() if PY2 else {}
					for param, paramvalue in node.attributes.items():
						if param == 'mode': continue 
						assert not param.startswith('_'), 'Parameter names cannot start with _'
						params[param] = paramvalue
			
				modeString = node.getAttribute('mode') or self.getText(node)

				if not modeString:
					if not params: continue # simply ignore <mode> as it's sometimes included in templates etc

					modeNamePattern = modesNode.getAttribute('modeNamePattern')
					if modeNamePattern:
						try:
							modeString = modeNamePattern.format(**params)
						except Exception as ex:
							raise UserError('Failed to populate modeNamePattern "%s" with parameters %s: %s in "%s"'%(modeNamePattern, params, ex, self.file))
					else:
						modeString = '_'.join(
							'%s=%s'%(k, v) if re.match('^([-0-9.]+|true|false|)$', v, flags=re.IGNORECASE) else v # include the key for numeric and boolean values
							for (k,v) in params.items())
				
					# Eliminate dodgy characters
					badchars = re.sub('[%s]+'%pysys.launcher.MODE_CHARS,'', modeString)
					if badchars: 
						log.debug('Unsupported characters "%s" found in test mode "%s" of %s; stripping them out', 
							''.join(set(c for c in badchars)), modeString, self.file)
					modeString = re.sub('[^%s]'%pysys.launcher.MODE_CHARS,'', modeString)
					
					if not modeString: raise UserError('Invalid mode: cannot be empty in \"%s\"'%self.file)
					
					# Enforce naming convention of initial caps
					modeString = modeString[0].upper()+modeString[1:]

				modeString = modeString.strip().strip('_') # avoid leading/trailing _'s and whitespace, since we'll add them when composing modes
				
				if modeString in result:
					if result[modeString] != params: raise UserError('Cannot redefine mode "%s" with parameters %s different to previous parameters %s in "%s"'%(modeString, params, result[modeString], self.file))
				else:
					result[modeString] = params
			# end of for <mode>

			# check that params are the same in each one to avoid mistakes
			if result:
				expectedparams = sorted(next(iter(result.values())).keys())
				for mode, params in result.items():
					if sorted(params.keys()) != expectedparams:
						raise UserError('The same mode parameter keys must be given for each mode under <modes>, but found %s != %s in "%s"'%(sorted(params.keys()), expectedparams, self.file))

			primary = modesNode.getAttribute('primary')
			if primary: # put the primary first if explicitly configured
				if primary not in result: raise UserError('Cannot find the specified primary mode "%s" in [%s] while loading "%s"'%(primary, ', '.join(result.keys()), self.file)) 
				result = {m: result[m] for m in sorted(result.keys(), key=lambda m: m != primary)}
			
			if prevModesForCombining is not None:
				if not result or not prevModesForCombining:
					result = prevModesForCombining or result
				else:
					# create the cross-product of these two mode matrices, i.e. result = prevModesForCombining * result
					newModes = result
					result = {}
					for modeA, paramsA in prevModesForCombining.items():
						for modeB, paramsB in newModes.items():
							params = dict(paramsA)
							params.update(paramsB) # newer "B" params take precedence if any keys as the same
							result[modeA+'_'+modeB] = params

			exclude = modesNode.getAttribute('exclude')
			if exclude:
				project = pysys.config.project.Project.getInstance()
				result = {m: params for m,params in result.items() if not pysys.utils.safeeval.safeEval(exclude, 
						extraNamespace={'mode': TestMode(m, params=params), 'project': project})}

		return [TestMode(k, params=v) for (k,v) in result.items()]

				
	def getClassDetails(self):
		'''Return the test class attributes (name, module, searchpath), contained in the class element.'''
		el = self.getSingleElement('class', optionalParents=['data'])
		if el:
			return [el.getAttribute('name'), el.getAttribute('module')]
		return [self.defaults.classname, self.defaults.module]

	def getExecutionOrderHint(self):
		e = self.getSingleElement('execution-order')

		r = None
		if e:
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


	def getUserData(self):
		# start with parent defaults, add children
		result = collections.OrderedDict(self.defaults.userData)
		for data in self.root.getElementsByTagName('data'):
			for e in data.getElementsByTagName('user-data'):
				key = e.getAttribute('name').strip()
				assert key, 'name= must be specified'
				assert key not in {'input', 'output', 'reference', 'descriptor', 'runner', 'log', 'project', 'lock'}, key # prevent names that we reserve for use by the basetest/processuser
				
				# NB: we don't use inspect.cleandoc here since it'd probably slow down descriptor loading and in 99% 
				# of for multi-line strings we will be stripping whitespace anyway so not a good use of time
				value = e.getAttribute('value')
				if not value and e.childNodes:
					value = '\n'.join(n.data for n in e.childNodes 
						if (n.nodeType in {n.TEXT_NODE,n.CDATA_SECTION_NODE}) and n.data)
				if value is None: value = ''
				try:
					value = self.project.expandProperties(value)
				except Exception as ex: # pragma: no cover
					raise UserError('Failed to resolve user-data value for "%s" in XML descriptor "%s": %s' % (key, self.file, ex))

				result[key] = value
				
		return result

			
	def getTestInput(self):
		node = self.getSingleElement('input', optionalParents=['data']) or self.getSingleElement('input-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.input
		
	def getTestOutput(self):
		node = self.getSingleElement('output', optionalParents=['data']) or self.getSingleElement('output-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.output

	def getTestReference(self):
		node = self.getSingleElement('reference', optionalParents=['data']) or self.getSingleElement('reference-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.reference

	def getRequirements(self):
		'''Return a list of the requirement ids, contained in the character data of the requirement elements.'''
		reqList = []			
		for node in self.root.getElementsByTagName('requirement'):
			if (node.getAttribute('id') or '').strip(): reqList.append(node.getAttribute('id').strip())

		# these used to always be below <traceability><requirements>..., but now we allow them directly under the root node 
		# (or anywhere the user wants)

		reqList = [x for x in self.defaults.traceability if x not in reqList]+reqList
		return reqList

	@staticmethod
	def getText(element):
		"""Utility method that reads text from the specified element and 
		strips leading/trailing whitespace from it. Returns an empty string if none. """
		t = u''
		if not element: return t
		for n in element.childNodes:
			if (n.nodeType in [element.TEXT_NODE, element.CDATA_SECTION_NODE]) and n.data:
				t += n.data
		return t.strip()

	def getSingleElement(self, tagName, parent=None, optionalParents=[]):
		"""Utility method that finds a single child element of the specified name and 
		strips leading/trailing whitespace from it. Returns None if not found. """
		t = u''
		if not parent: parent = self.root
		nodes = parent.getElementsByTagName(tagName)
		if len(nodes) == 0: return None
		if len(nodes) > 1: 
			raise UserError('Expected one element <%s> but found more than one in %s' % (tagName, self.file))
		if nodes[0].parentNode.tagName not in ['pysystest', 'pysysdirconfig']+optionalParents: 
				raise UserError("Element <%s> is not permitted under <%s> of \"%s\""%(tagName, nodes[0].parentNode.tagName, self.file))
		return nodes[0]

	def getElementTextOrDefault(self, tagName, default=None, parent=None, optionalParents=[]):
		"""Utility method that finds a single child element of the specified name and 
		strips leading/trailing whitespace from it. Returns an empty string if none. """
		t = u''
		node = self.getSingleElement(tagName, parent=parent, optionalParents=optionalParents)
		if node is None: return default
		return self.getText(node)

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

	:ivar pysys.config.project.Project ~.project: The `pysys.config.project.Project` instance. 
	
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
		
		:return: List of L{pysys.config.descriptor.TestDescriptor} objects 
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
		ignoreSet = set(OSWALK_IGNORES+[DEFAULT_INPUT, DEFAULT_OUTPUT, DEFAULT_REFERENCE])
		
		if project.properties.get('pysysTestDescriptorFileNames') or DEFAULT_DESCRIPTOR != ['pysystest.xml']:
			# compatibility mode
			descriptorSet = set([s.strip() for s in project.getProperty('pysysTestDescriptorFileNames', default=','.join(DEFAULT_DESCRIPTOR)).split(',')])
		else:
			descriptorSet = None
		
		assert project.projectFile != None
		log = logging.getLogger('pysys.launcher')

		# although it's highly unlikely, if any test paths did slip outside the Windows 256 char limit, 
		# it would be very dangerous to skip them (which is what os.walk does unless passed a \\?\ path), 
		# so must use long-path-safe - but need to re-encode from unicode string back to bytestring in Python 2
		i18n_reencode = PREFERRED_ENCODING if PY2 and isinstance(dir, str) else None
		
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
			# see also console_make.py which needs similar logic
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

			if descriptorSet is None: 
				intersection = [f for f in files if f.lower().startswith('pysystest.')]
			else: # compatibility mode
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
					raise Exception("Error reading XML descriptor from '%s': %s - %s" % (descriptorfile, e.__class__.__name__, e))

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
		""" Parses a single descriptor file (typically an XML file, or a file of another type containing XML) for a 
		testcase or directory configuration and returns the resulting descriptor. 
		
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
