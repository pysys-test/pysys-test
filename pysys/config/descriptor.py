#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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
(``pysystest.*``) or directory (``pysysdirconfig.xml``), and the `DescriptorLoader <pysys.config.descriptor.DescriptorLoader>` 
class allows customization of the test discovery process. 
"""

from __future__ import print_function
import os.path, logging, xml.dom.minidom
import collections
import copy
import locale
import inspect
import importlib
import time

import pysys
from pysys.constants import *
from pysys.exceptions import UserError
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe, pathexists
from pysys.utils.pycompat import isstring

log = logging.getLogger('pysys.config.descriptor')

class TestDescriptor(object):
	"""Descriptor metadata for an individual testcase (``pysystest.*``) or defaults for tests under a directory 
	subtree (``pysysdirconfig.xml``); see :doc:`/pysys/TestDescriptors`. 
	
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
	
	:ivar list[TestMode] ~.modes: A list of the user defined modes the testcase can be run in. 

	:ivar TestMode ~.mode: Specifies which of the possible modes this descriptor represents or None if the 
		the descriptor has no modes. This field is only present after the 
		raw descriptors have been expanded into multiple mode-specific descriptors. 
		Note that after a descriptor is created from the on-disk file, the `mode` attribute is not set until 
		the later phase when multi-mode descriptors are cloned and expanded based on the selected modes. 
	
		You can use ``descriptor.mode.params`` to get the parameter dictionary for this mode, 
		and ``descriptor.mode.isPrimary`` to find out of this is a primary mode. 
	
	:ivar str ~.classname: The Python classname to be executed for this testcase.
	
	:ivar str ~.module: The path to the python module containing the testcase class. Relative to testDir, or an absolute path.
		If not set, the class is looked up in the PYTHONPATH. 
	
	:ivar str ~.input: The path to the input directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar str ~.output: The path to the output parent directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar str ~.reference: The path to the reference directory of the testcase. Relative to testDir, or an absolute path.
	
	:ivar list ~.traceability: A list of the requirements covered by the testcase, typically keywords or bug/story ids.
	
	:ivar list[str] ~.authors: A list of the names or user ids of people who contributed to the test. 

	:ivar str ~.created: The date when the test was created in yyyy-mm-dd format. 
	
	:ivar float ~.executionOrderHint: A float priority value used to determine the 
		order in which testcases will be run; higher values are executed before 
		low values. The default is 0.0. 
	
	:ivar bool ~.isDirConfig: True if this is a directory configuration, or False if 
		it's a normal testcase. 
	
	:ivar dict[str,obj] ~.userData: A Python dictionary that can be used for storing user-defined data 
		in the descriptor. In a pysystest.py, this can be populated by a ``__pysys_user_data__`` dictionary, e.g. 
		``__pysys_user_data__ = {"key": "val ${projectProperty}"}`` or ``__pysys_user_data.key__ = "val"``.
	"""

	__slots__ = 'isDirConfig', 'file', 'testDir', 'id', 'type', 'state', 'title', 'purpose', 'groups', 'modes', 'mode', \
		'classname', 'module', 'input', 'output', 'reference', 'traceability', 'executionOrderHint', 'executionOrderHintsByMode', \
		'authors', 'created', \
		'skippedReason', 'idWithoutMode', '_defaultSortKey', 'userData', '_makeTestTemplates', '_descriptorLoaderPlugins',

	def __init__(self, file, id, 
		type="auto", state="runnable", title=u'', purpose=u'', groups=[], modes=[], 
		classname=DEFAULT_TESTCLASS, module=DEFAULT_MODULE, 
		input=DEFAULT_INPUT, output=DEFAULT_OUTPUT, reference=DEFAULT_REFERENCE, 
		traceability=[], executionOrderHint=0.0, skippedReason=None, 
		authors=[], created=None,
		testDir=None, 
		isDirConfig=False, userData=None
		):

		self.isDirConfig = isDirConfig
		if not isDirConfig:
			assert file, [file, id]
			self.testDir = fromLongPathSafe(testDir or os.path.dirname(file))

		self.file = file
		self.setId(id)

		if skippedReason: state = 'skipped'
		if state=='skipped' and not skippedReason: skippedReason = '<unknown skipped reason>'

		self.type = type
		self.state = state
		self.title = title
		self.purpose = purpose
		# copy groups/modes so we can safely mutate them later if desired
		self.groups = list(groups)
		if len(modes)>0 and any(not isinstance(m, TestMode) for m in modes):
			# simple strings were passed in; convert them
			modes = [(m if isinstance(m, TestMode) else TestMode(m)) for m in modes]
		else:
			modes = list(modes)
		
		if len(modes)>0 and (not any(m.isPrimary for m in modes)):
			modes = [TestMode(modes[0], isPrimary=True, params=modes[0].params)]+modes[1:]

		self.modes = modes

		self.authors = authors
		self.created = created
		if created and not re.match('[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$', created):
			raise UserError('Invalid created date "%s", must be yyyy-mm-dd format, in file "%s"'%(created, file))

		
		self.classname = classname
		assert classname, 'Test descriptors cannot set the classname to nothing'

		if not module: self.module = None
		elif module.endswith('.py') or module == 'PYTHONPATH': self.module = module
		else: self.module = module+'.py'
		
		
		self.input = input
		self.output = fromLongPathSafe(output) # just in case descriptors were loaded dynamically and contain absolute \\?\ paths on windows
		self.reference = reference

		self.traceability = traceability
		self.executionOrderHint = executionOrderHint
		self.skippedReason = skippedReason
		
		# NB: self.mode is set after construction and 
		# cloning for each supported mode 
		
		self.userData = collections.OrderedDict() if userData is None else userData
	
	def setId(self, id):
		"""
		Change the id of this descriptor. 

		This can be used by `DescriptorLoader` or a loader plugin to modify the id of a descriptor just after it has been parsed. 

		Use this insteaad of assigning directly to the id field. 

		:return: Returns ``self`` to allow fluent usage. 
		"""
		self.id = id
		self.idWithoutMode = self.id

		# for internal use only (we cache this to speed up sorting based on path), 
		# and only for tests not dir configs; 
		# convert to lowercase to ensure a canonical sort order on case insensitive OSes; 
		# add id to be sure they're unique (e.g. including mode)
		if self.file: self._defaultSortKey = self.file.lower()+'/'+self.id

		return self


	def _getTestFile(self):
		# undocumented API currently
		# Gets the file containing the test logic - typically a .py file, but could be some other format e.g. .java (but not XML)
		# Usually relative to testDir, but may be an absolute path
		if self.file.endswith('.xml') and self.module and self.module != 'PYTHONPATH':
			return self.module
		
		if self.file.startswith(self.testDir): return self.file[len(self.testDir)+1:]
		return self.file
	
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
		d['descriptorFile'] = self.file
		d['type'] = self.type
		d['state'] = self.state
		d['skippedReason'] = self.skippedReason
		d['title'] = self.title
		d['purpose'] = self.purpose
		d['groups'] = self.groups
		d['authors'] = self.authors
		d['created'] = self.created
		def modeParamsDict(m):
			x = m.params
			if m.isPrimary:
				x = dict(x)
				x['isPrimary'] = True
			return x
		d['modes'] = {str(m):modeParamsDict(m) for m in self.modes}
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
		# Some of these are only worth printing when there's actually something to show, and for legacy things like 
		# type/state, when a non-default value is selected
		
		s=    "Test id:           %s\n" % self.id
		reltestdir = self.testDir if not self.isDirConfig else '' # relative to current dir is most useful
		if reltestdir.lower().replace('\\','/').startswith(os.getcwd().lower().replace('\\','/')+'/'): reltestdir = reltestdir[len(os.getcwd())+1:]
		s=s+"Test directory:    %s\n" % reltestdir # use OS slashes to facilitate copy+paste
		if self.type != 'auto': s=s+"Test type:         %s\n" % self.type
		if self.state != 'runnable' and not self.skippedReason:
			s=s+"Test state:        %s\n" % self.state
		if self.skippedReason: s=s+"Test skip reason:  %s\n" % self.skippedReason
		s=s+"Test title:        %s\n" % self.title
		if self.purpose:
			s=s+"Test purpose:      "
			purpose = self.purpose.split('\n')
			for index in range(0, len(purpose)):
				if index == 0: s=s+"%s\n" % purpose[index]
				if index != 0: s=s+"                   %s\n" % purpose[index] 

		if self.created or self.authors:
			s=s+"Test created:      %s; authors: %s\n" % (self.created or '?', ', '.join(self.authors))

		s=s+"Test groups:       %s\n" % (u', '.join((u"'%s'"%x if u' ' in x else x) for x in self.groups) or u'<none>')
		
		def modeNameToString(m):
			x = "'%s'"%m if ' ' in m else m
			return x

		modeDelim = '\n --> ' if any(getattr(m, 'params', None) for m in self.modes) else ', '

		longestmode = max(len(modeNameToString(m)) for m in self.modes) if self.modes else 0
		def modeToString(m):
			x = modeNameToString(m)
			if modeDelim != ', ':
				x = ("%-"+str(longestmode+1)+"s")%x
			if getattr(m, 'params', None):
				x += '{%s}'%', '.join('%s=%r'%(k,v) for (k,v) in m.params.items())
			if getattr(m, 'isPrimary', False) and len(self.modes)>1: x=x+' [PRIMARY]'
			return x.strip()
		
		if getattr(self, 'mode',None): # multi mode per run
			s=s+"Test mode:         %s\n" % modeToString(self.mode)
		else: # print available modes instead
			s=s+("Test modes:        %s%s\n") % (modeDelim if '\n' in modeDelim else '', modeDelim.join(modeToString(x) for x in self.modes) or u'<none>')

		s=s+"Test order hint:   %s\n" % (
			u', '.join('%s'%hint for hint in self.executionOrderHintsByMode) # for multi-mode tests
			if hasattr(self, 'executionOrderHintsByMode') else self.executionOrderHint)	

		s=s+"Test classname:    %s; module: %s\n" % (self.classname, self.module)
		if self.input not in [DEFAULT_INPUT, '.', '!Input_dir_if_present_else_testDir!', '!INPUT_DIR_IF_PRESENT_ELSE_TEST_DIR!']: s=s+"Test input:        %s\n" % self.input
		if self.output != DEFAULT_OUTPUT: s=s+"Test output:       %s\n" % self.output
		if self.reference != DEFAULT_REFERENCE: s=s+"Test reference:    %s\n" % self.reference
		if self.traceability:
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

class TestModesConfigHelper:
	"""
	A helper class that is passed to the lambda which defines test modes in a pysystest configuration. It provides access to 
	the list of inherited modes, to project properties and also helper functions for combining multiple mode lists into 
	one and for configuring a collection of modes as primary modes. 
	
	See :doc:`/pysys/UserGuide` for detailed information about what you can do with PySys modes. 
	
	:ivar list[dict[str,obj]] ~.inheritedModes: A list of the inherited modes, each defined by a dictionary containing a ``mode`` 
		key and any number of additional parameters. 
	:ivar ~.constants: A reference to `pysys.constants` which can be used to access constants such as ``IS_WINDOWS`` for 
		platform-dependent mode configuration. 
	:ivar ~.pysys: A reference to the `pysys` module. 
	:ivar callable[str] import_module: A reference to the Python ``importlib.import_module`` function that can be used 
		if you need to access functions from additional modules such as ``sys``, ``re``, etc. 
	:ivar pysys.config.project.Project ~.project: The project configuration, from which you can read properties. 
	:ivar str ~.testDir: The test directory, i.e. the directory containing the ``pysystest.*`` file where this modes 
		configuration is defined. This is not available when defining modes in ``pysysdirconfig``, but only when the mode 
		configuration is directly in the ``pysystest.*`` file. 

	"""
	def __init__(self, inheritedModes, project, testDir):
		self.inheritedModes = inheritedModes
		self.project = project
		self.constants = pysys.constants
		self.import_module = importlib.import_module
		self.pysys = pysys
		self.os = os
		self.testDir = testDir

	def makeAllPrimary(self, modes):
		"""
		Modifies the specified list (or dict) of modes so that all of them have isPrimary=True. 
		
		By default only the first mode in the mode list is "primary", so the test will only run in that one mode by 
		default during local development (unless you supply a ``--modes`` or ``--ci`` argument). This is optimal when 
		using modes to validate the same behaviour/conditions in different execution environments e.g. 
		browsers/databases etc. However when using modes to validate different *behaviours/conditions* (e.g. testing 
		out different command line options) using a single PySysTest class, then you should have all your modes as 
		"primary" as you want all of them to execute by default in a quick local test run. 
		
		You would typically combine test-specific behaviour modes with any inherited execution environment modes like 
		this::
		
			lambda modes: modes.createModeCombinations(
				helper.inheritedModes,
				helper.makeAllPrimary(
					{
						'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
						'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
						'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
					}, 
			)
		
		:param list[dict[str,obj]]|dict[str,dict[str,obj]] modes: A list or dict of modes to be made primary.
		:return: A list[dict[str,obj]] containing the modes, each with isPrimary set to true. 
		
		"""
		if isinstance(modes, dict):
			modes = [{**{'mode':k}, **v} for k, v in modes.items()]
		for m in modes: m['isPrimary'] = True
		return modes

	def createModeCombinations(self, *dimensions):
		"""
		Generates a mode list containing all the combinations from each mode list passed into the function. 
		
		For example, you could combine a list of inherited modes (defined in parent directories' ``pysysdirconfig.xml`` 
		files), with a second dimension containing modes for each database you want to test with and a third dimension with 
		modes for each web browser. The result would be a single (flat) list containing modes, with names and parameter 
		dictionaries automatically merged together from each input dimension::
				
			lambda helper: helper.createModeCombinations(
				helper.inheritedModes,
				{
					'MySQL':  {'db': 'MySQL',  'dbTimeoutSecs':60}, 
					'SQLite': {'db': 'SQLite', 'dbTimeoutSecs':120},
					'Mock':   {'db': 'Mock',   'dbTimeoutSecs':30},
				},
				
				# can use dict or list format for each mode list, whichever is more convenient: 
				[ 
					{'browser':'Chrome'}, # if mode is not explicitly specified it is auto-generated from the parameter(s)
					{'browser':'Firefox'},
				]
				)
		
		would generate a list of modes named::
		
			MySQL_Chrome
			MySQL_Firefox
			SQLite_Chrome
			SQLite_Firefox
			Mock_Chrome
			Mock_Firefox
		
		NB: By default the first mode in each dimension is designated a *primary* mode (one that executes by default 
		when no ``--modes`` or ``--ci`` argument is specified), but this can be overridden by setting ``'isPrimary': True/False`` 
		in the dict for any mode. When mode dimensions are combined, the primary modes are AND-ed together, 
		i.e. any where *all* mode dimensions will be designated primary. 
		So in the above case, since MySQL and Chrome are automatically set as 
		primary modes, the MySQL_Chrome mode would be the (only) primary mode returned from this function.
		When using modes for different execution environments/browsers etc you probably want only 
		the first (typically fastest/simplest/most informative) mode to be primary; on the other hand if using modes to 
		re-use the same PySysTest logic for against various behavioural tests (different input files/args etc) 
		you should usually set all of the modes to be 
		primary so that all of them are executed in your test runs during local development. 

		A common use case is to combine inherited modes from the parent pysysdirconfigs with a list of modes specific to 
		this test::
		
			lambda helper: helper.createModeCombinations(
				helper.inheritedModes,
				
				helper.makeAllPrimary(
					{
						'Usage':         {'cmd': ['--help'], 
							'expectedExitStatus':'==0', 'expectedMessage':None}, 
						'BadPort':       {'cmd': ['--port', '-1'],  
							'expectedExitStatus':'!=0', 'expectedMessage':'Server failed: Invalid port number specified: -1'}, 
						'SetPortTwice':  {'cmd': ['--port', '123', '--config', helper.testDir+'/myserverconfig.json'], 
							'expectedExitStatus':'!=0', 'expectedMessage':'Server failed: Cannot specify port twice'}, 
					}), 
			)
		
		For simplicity this common case can be expressed with the more concise syntax::
		
			__pysys_parameterized_test_modes__ = {
					'Usage':        {'cmd': ['--help'], 'expectedExitStatus':'==0'}, 
					'BadPort':      {'cmd': ['--port', '-1'],  'expectedExitStatus':'!=0'}, 
					'MissingPort':  {'cmd': [],  'expectedExitStatus':'!=0'}, 
				}

		NB: For efficiency reasons, don't use the ``createModeCombinations`` method in your configuration if you are 
		*just* using the inherited modes unchanged. 
		
		:param list[dict[str,obj]]|dict[str,dict[str,obj]] dimensions: Each argument passed to this function is a list of 
			modes, each mode defined by a dict which may contain a ``mode`` key plus any number of parameters. 
			Alternatively, each dimension can be a dict where the mode is the key and the value is a parameters dict. 
			
		:return: A list[dict[str,obj]] containing the flattened list of modes consisting of all combinations of the 
			passed in. Mode names and parameter dictionaries will be merged. 
			For example: ``[{"mode":"MyMode", "param1":100}, {"mode": "myMode2", "param1":200}]``. 
			The returned list can be further manipulated using Python list comprehensions (e.g. to exclude certain 
			combinations) if desired. 
			
		.. versionadded:: 2.1
		"""
		if len(dimensions) == 1: return dimensions[0]
		
		current = {} # key=mode name value=params
		for dimension in dimensions:
			prevModesForCombining = None if not current else current

			current = {}
			if isinstance(dimension, dict):
				dimension = [{**{'mode':k}, **v} for k, v in dimension.items()]

			for mode in dimension:
				modeString, params = _XMLDescriptorParser.splitModeNameAndParams(mode, project=self.project)
				current[modeString] = mode
			# end for mode
			
			# ensure at least one is primary in each dimension, else we'd lose the primary-ness when AND-ing them together
			if current and not any(m.get('isPrimary', False) for m in current.values()): 
				next(iter(current.values()))['isPrimary'] = True

			if prevModesForCombining is not None:
				if not current or not prevModesForCombining:
					current = prevModesForCombining or current
				else:
					newModes = current
					current = {}
					for modeA, paramsA in prevModesForCombining.items():
						for modeB, paramsB in newModes.items():
							isPrimary = paramsA.get('isPrimary', False) and paramsB.get('isPrimary', False)
							params = dict(paramsA)
							params.update(paramsB) # newer "B" params take precedence if any keys as the same
							# for simplicity, just include it with params here
							params['isPrimary'] = isPrimary
							current[modeA.strip('_')+'_'+modeB.strip('_')] = params
		return [{**{'mode':modeString}, **params} for modeString, params in current.items()]

	def combineModeDimensions(self, *dimensions):
		"""
		Old name for the `createModeCombinations` method. 
		"""
		return self.createModeCombinations(*dimensions)


class TestMode(str): # subclasses string to retain compatibility for tests that don't use mode parameters
	"""Represents a mode that a test can run in in a `TestDescriptor`, and optionally a dict of parameters that define 
	that mode. 
	
	To create one::
	
		mode = TestMode('MyMode', {'param1': 'value1'})
	
	See the ``mode`` parameter/field in `TestDescriptor` where this class is used. 
	
	This class is immutable, so create a new instance if you want to change something. 
	
	The mode values can be of any type as long as it is pickleable (see Python's `pickle` module for more information). 
	Standard Python types like strings, dicts etc are fine. 

	For convenience and compatibility, this TestMode subclasses a string holding the mode. 
	
	:ivar str ~.name: The name of the mode as a string. 

	:ivar dict[str,obj] ~.params: A dictionary of parameters associated with this mode. The parameters are available to 
		the test (as ``self.mode.params``) and also assigned as instance fields on the test class when it 
		runs in this mode. 
		
	:ivar bool ~.isPrimary: Indicates whether this is a primary mode, 
		one that executes by default even when not explicity requested with a command line option such as ``--modes=ALL``. 

	.. versionadded:: 2.0

	"""
	__slots__ = ['__params', '__isPrimary', '__name']
	
	def __new__(cls,s,params=None, isPrimary=False):
		self = str.__new__(cls,s)
		self.__name = s
		if params is None: params = {}
		self.__params = params
		assert 'isPrimary' not in params, repr(params)
		self.__isPrimary = isPrimary
		return self

	@property
	def params(self):
		return self.__params

	@property
	def isPrimary(self):
		return self.__isPrimary
	
	@property
	def name(self):
		return self.__name
	
	def __repr__(self):
		return self.name+str(self.__params)+('[PRIMARY]' if self.__isPrimary else '')
	
class _XMLDescriptorParser(object):
	'''NOT PUBLIC API - use L{DescriptorLoader._parseTestDescriptor} instead. 
	
	:meta private:
	
	Helper class to parse an XML test descriptor - either for a testcase, 
	or for defaults for a (sub-)directory of testcases.

	If the file is/contains XML the class uses the minidom DOM (Document Object Model) non-validating
	parser to provide accessor methods to return element attributes	and character
	data from the test descriptor file. The class is instantiated with the filename
	of the test descriptor. It is the responsibility of the user of the class to
	call the unlink() method of the class on completion in order to free the memory
	used in the parsing.
	
	If not, it uses __pysys_XXX__ dunders (Python-style but also designed to work fine in other languages whether in 
	comments e.g. /* ... */  or even as string literals, provided there are no backslash escapes to worry about).
	
	:param bytes fileContents: Used only for testing purposes - to measure load times without any disk activity. 
	'''

	KV_PATTERN = '__pysys_%s__'
	
	__IMPORT_EXPR = b'\nimport ' if os.linesep.endswith('\n') else b'\rimport ' # the former works for windows+linux (regardless of ending), the latter for mac
	__PYTHON_PYSYS_DUNDER_EXPR = b'\n__pysys_' if os.linesep.endswith('\n') else b'\r__pysys_'
	__DISABLE_PYTHON_DESCRIPTOR_PARSING = os.getenv('PYSYS_DISABLE_PYTHON_DESCRIPTOR_PARSING','').lower()=='true' # undocumented, just for testing 

	parseTimeXML = 0.0
	parseTimePython = 0.0

	def __init__(self, xmlfile, istest=True, parentDirDefaults=None, project=None, xmlRootElement=None, fileContents=None):
		assert project
		self.file = xmlfile
		if len(xmlfile) < 256: self.file = fromLongPathSafe(self.file)# used for error messages etc
		
		self.dirname = os.path.dirname(xmlfile)
		self.istest = istest
		self.defaults = (project._defaultDirConfig or self.DEFAULT_DESCRIPTOR) if parentDirDefaults is None else parentDirDefaults
		roottag = 'pysystest' if istest else 'pysysdirconfig'
		if not os.path.exists(xmlfile):
			raise UserError("Unable to find supplied descriptor \"%s\"" % self.file)
		self.project = project

		self.kvDict = {}
		
		if xmlRootElement: # used when parsing from project XML rather than directly from a standalone file
			self.doc = None
			self.root = xmlRootElement
			assert xmlRootElement.tagName == 'pysysdirconfig', xmlRootElement.tagName
			return
		
		starttime = time.monotonic()
		if istest and not xmlfile.endswith('.xml'):
			if fileContents is None:
				# Open in binary mode since we don't know the encoding - we'll rely on the XML header and/or Python header to tell us if it's anything unusual
				with open(xmlfile, 'rb') as xmlhandle:
					fileContents = xmlhandle.read()
								
			# Find it within a file of another type e.g. pysystest.py
			if xmlfile.endswith('.py') and not _XMLDescriptorParser.__DISABLE_PYTHON_DESCRIPTOR_PARSING:

				# NB Doing a full python parse, ignoring the import statements onwards, is up to 14% faster(!) 
				# (for large size/complexity) than the regex approach - and of course more idiomatic for Python developers
				
				pythonHeader = fileContents
				
				# Optimize for speed (and to reduce unnecessary failures) by stripping out everything from the imports onwards
				# assume platform native line endings, for performance reasons - if incorrect, just means we miss the perf optimization
				# decent speed up from not using regex's here

				# we could also search for "from XXX import ..." but that's harder to match without regex's so don't bother as it would slow down the common case
				
				firstImportIndex = pythonHeader.find(_XMLDescriptorParser.__IMPORT_EXPR) # the first "\nimport " is a pretty clear sign of the imports beginning
				# nb: give up on optimization if there are "__pysys_" lines below the imports
				if firstImportIndex > 0 and _XMLDescriptorParser.__PYTHON_PYSYS_DUNDER_EXPR not in fileContents[firstImportIndex:]:
					pythonHeader = pythonHeader[:firstImportIndex]
				
				runpycode = compile(pythonHeader, xmlfile, 'exec')
				runpy_namespace = {}
				exec(runpycode, runpy_namespace)
				for k in runpy_namespace:
					if k.startswith('__pysys_'):
						if not k.endswith('__'): raise UserError(f'Incorrect key format for "{k}" (should end with "__") in "{self.file}"')
						self.kvDict[k[len('__pysys_'):].rstrip('_')] = runpy_namespace[k]
				del runpy_namespace
			else: # non-Python files, fall back to a general purpsoe Python-like syntax
			
				# must be at the start of a line, i.e. not after a comment
				# we do allow raw strings
				for m in re.finditer(
						(f'^[ \\t]*{self.KV_PATTERN.rstrip("__")%"(?P<key>[^ =]+)"} *= *(?:(?P<rawstring>[r@])?(' # r for python raw strings, @ for C#
							+'|'.join([
								'(?P<value1>(-?[0-9+-][0-9.]+|[T]rue|[F]alse))', # number/boolean literal, would be a shame for it to have to be quoted
								'"""(?P<value2>(?:[^"]|"{1,2}(?!"))*)"""',
								'"(?P<value3>[^"]*)"',
							])
							+') *($|[;#\\n\\r]))?' # ensure there's no attempt to concatenate something else; we make the string matching part optional so we can give a nice error if it goes wrong
							).encode('ascii'), 
						fileContents, flags=re.DOTALL + re.MULTILINE): 
					k = m.group('key').decode('ascii', errors='replace')
					if not k.endswith('__'): raise UserError(f'Incorrect key format for "{self.KV_PATTERN.rstrip("_") % k}" in "{self.file}"')
					k = k.rstrip('_')
				
					if k in self.kvDict: raise UserError('Duplicate key "{self.KV_PATTERN % k}__" in "{self.file}"')
					value = m.group('value1') or m.group('value2') or m.group('value3')
					if value is None:
						raise UserError(f'Cannot parse the value for {self.KV_PATTERN % k} in {self.file}; after the "=" you should use r"""...""", "..." or a numeric/boolean literal')
					if (not m.group('rawstring')) and b'\\' in value: raise UserError(f'Cannot use backslash escape sequences for {self.KV_PATTERN % k} value (unless using a raw r"""...""" string); cannot parse "{self.file}"')
					if k != 'xml_descriptor': # we keep xml descriptors as bytes so we can use the correct encoding
						value = value.decode('utf-8', errors='replace')
					self.kvDict[k] = value

			if 'title' not in self.kvDict and 'xml_descriptor' not in self.kvDict: raise UserError(f'Cannot find mandatory {self.KV_PATTERN % "title"} specifier for this test in {self.file} (found: {list(self.kvDict.keys())})')
			xmlcontents = self.kvDict.pop('xml_descriptor', '').strip() # not likely to be used for .py files, but might be nice for some others
		else:
			xmlcontents = fileContents # usually None, unless this is a microbenchmark performance test
		
		try:
			if xmlcontents:
				self.doc = xml.dom.minidom.parseString(xmlcontents)
			elif xmlcontents == None:
				self.doc = xml.dom.minidom.parse(xmlfile)
			else:
				self.doc = self.root = None
				return
				
		except Exception as ex:
			raise UserError("Invalid XML in descriptor '%s': %s" % (self.file, ex))
		else:
			if self.doc.getElementsByTagName(roottag) == []:
				raise UserError("No <%s> element supplied in XML descriptor '%s'"%(roottag, self.file))
			else:
				self.root = self.doc.getElementsByTagName(roottag)[0]
		if xmlfile.endswith('.xml'):
			_XMLDescriptorParser.parseTimeXML += time.monotonic()-starttime
		else:
			_XMLDescriptorParser.parseTimePython += time.monotonic()-starttime

	@staticmethod
	def parse(xmlfile, istest=True, parentDirDefaults=None, project=None, **kwargs):
		"""
		Parses the test/dir descriptor in the specified path and returns the 
		TestDescriptor object. 
		
		:param istest: True if this is a ``pysystest.*`` file, false if it is 
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

		if self.root:
			for attrName, attrValue in self.root.attributes.items():
				if attrName not in ['state', 'type', 'authors', 'created']:
					raise UserError('Unknown attribute "%s" in XML descriptor "%s"'%(attrName, self.file))
		cls, pymodule = self.getClassDetails()
		
		if pymodule is None and self.istest: # default setting means auto-detect (nb: NOT the same as pymodule='' which means to use the PYTHONPATH)
			if self.file.endswith('.py'):
				pymodule = os.path.basename(self.file)
			elif cls and '.' in cls: # if the Python class is X.Y it's probably got a package name and therefore PYTHONPATH (could be a nested class inside a run.py but pretty unlikely)
				pymodule = 'PYTHONPATH'
			else:
				pymodule = DEFAULT_MODULE # else run.py
		
		
		
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
										userData={k:self.project.expandProperties(v) for k,v in self.getUserData().items()},
										authors=[x.strip() for x in 
											(self.kvDict.pop('authors', None) or (self.root.getAttribute('authors') if self.root else '') 
											).split(',') if x.strip()],
										created=self.kvDict.pop('created', None) or (self.root.getAttribute('created') if self.root else None) or None,
										isDirConfig=not self.istest)
		
		if self.kvDict and os.getenv('PYSYS_IGNORE_UNKNOWN_DESCRIPTOR_FIELDS','').lower()!='true': # should all have been popped during parsing
			raise UserError(f'Unknown {self.KV_PATTERN % "KEY"} key(s) in test descriptor "{self.file}": {", ".join(self.kvDict.keys())}')
		
		if not self.istest:
			# not an official/public part of the descriptor spec, so don't have it in the constructor signature
			t._makeTestTemplates = self._parseTestMakerTemplates()
			t._descriptorLoaderPlugins = getattr(self.defaults, '_descriptorLoaderPlugins', [])+self._parseDescriptorLoaderPlugins()
		
		return t

	def _parseDescriptorLoaderPlugins(self):# not public API, do not use
		plugins = []
		for node in self.root.getElementsByTagName('descriptor-loader-plugin'):
			from pysys.config.project import _XMLProjectParser
			cls, optionsDict = _XMLProjectParser._parseClassAndConfigDictImpl(self.__expandPropertiesImplFromProject, node, defaultClass=None)
			pluginKey = (cls, tuple(optionsDict.items())) # hashable
			plugins.append( (pluginKey, cls, optionsDict) )
		return plugins
	def __expandPropertiesImplFromProject(self, value, default, name=None): # hack to allow us to use _parseClassAndConfigDict from here - simulates api of _XMLProjectParser
		# setting default=None means we can't use <property default="...">" attributes here, but that's a price worth paying at least for now
		return self.project.expandProperties(value)

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
				if not r1 or not r2: raise UserError("Each maker-template <replace> element requires both a regex= and a with= attribute, in \"%s\""%self.file)
				t['replace'].append( (r1, r2) )
			templates.append(t)

		for e in self.root.getElementsByTagName('set-default-maker-template'):
			# for ease of processing, set the name to a fixed sentinel value so that the normal template handling logic can apply and the latest one will always override it
			templates.append({'name':'set-default-maker-template', 'set-default-maker-template': e.getAttribute('name')})

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
		id = self.defaults.id + self.kvDict.pop('id-prefix','')+self.getElementTextOrDefault('id-prefix', default='')
		
		for c in u'\\/:~#<>':
			# reserve a few characters that we might need for other purposes; _ and . can be used however
			if c in id:
				raise UserError('The <id-prefix> is not permitted to contain "%s"; error in "%s"'%(c, self.file))
		
		if self.istest: id = id+os.path.basename(self.dirname)
		
		return id

	def getType(self):
		'''Return the type attribute of the test element - mostly just legacy now.'''
		if not self.root: return self.defaults.type
		type = self.root.getAttribute("type") or self.defaults.type
		if type not in ["auto", "manual"]:
			raise UserError("The type attribute of the test element should be \"auto\" or \"manual\" in \"%s\""%self.file)
		return type

	def getState(self):
		'''Return the state attribute of the test element - mostly just legacy now.'''
		if not self.root: return self.defaults.state
		state = self.root.getAttribute("state")	 or self.defaults.state
		if state not in ["runnable", "deprecated", "skipped"]: 
			raise UserError("The state attribute of the test element should be \"runnable\", \"deprecated\" or \"skipped\" in \"%s\""%self.file)
		return state 

	def getSkippedReason(self):
		r = self.kvDict.pop('skipped_reason', None)
		if r is not None:
				if not r: raise UserError('Missing value for skipped reason in "{self.file}"')
				return r

		if self.root:
			for e in self.root.getElementsByTagName('skipped'):
				r = (e.getAttribute('reason') or '').strip() 
				# make this mandatory, to encourage good practice
				if not r: raise UserError('Missing reason= attribute in <skipped> element of "{self.file}"')
				return r

		return self.defaults.skippedReason

	def getTitle(self):
		# PySys 1.6.1 gave an error if <description> was missing, but a default if <title> was missing, and permitted empty string. So don't be too picky. 

		result = self.kvDict.pop('title', None) or self.getElementTextOrDefault('title', optionalParents=['description'])
		if result is None and self.istest: result = self.getID() # falling back to the ID is better than nothing
		
		result = result.replace('\n',' ').replace('\r',' ').replace('\t', ' ').strip().rstrip('.')
		if '  ' in result: result = re.sub('  +', ' ', result)

		if len(result)==0 and self.istest: result = self.getID() # falling back to the ID is better than nothing

		return result
				
	def getPurpose(self):
		result = self.kvDict.pop('purpose', None) or self.getElementTextOrDefault('purpose', optionalParents=['description'])
		if result is None: result = self.defaults.purpose
		
		if not result: return result
		return inspect.cleandoc(result.replace('\r','').replace('\t', '  ')).strip()
				
	def getGroups(self):
		groupList = []
		
		groups = self.kvDict.pop('groups', None)
		if isinstance(groups, str):
			groups = groups.replace(' ','').split(';')
			groupList = [g for g in groups[0].split(',') if g]
			if len(groups) > 1 and groups[1].lower() not in ['inherit=true', 'inherit=false']:
				raise UserError(f'Invalid inherit= specifier - groups should be in the form "my-group1, mygroup2, ...; inherit=true/false" in descriptor "{self.file}"')
			if len(groups)>1 and groups[1].lower() == 'inherit=false': return groupList
		else:
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
	
		
	@staticmethod 
	def splitModeNameAndParams(mode, project):
		"""
		Returns (modename, params). Auto-generates a mode name if one is not already provided. 
		
		WARNING: The mode dict is mutated by this method. 
		"""
		
		if isinstance(mode, TestMode): # just for the parameterized test modes use case
			modeString = mode.name
			params = dict(mode.params)
			params['isPrimary'] = mode.isPrimary
			mode = params
		else:
			assert isinstance(mode, dict), 'Each mode must be a {...} dict but found unexpected object %r (%s)'%(mode, mode.__class__.__name__)

			modeString = mode.pop('mode', None)
			if modeString: return modeString, mode

			# Auto-generate mode string
			
			assert len(mode) != 0, 'Must provide a name and/or params for every mode dictionary'
			modeString = '_'.join(
				'%s=%s'%(k, v) if (not isinstance(v, str) or re.match('^([-0-9.]+|true|false|)$', v, flags=re.IGNORECASE)) else v # include the key for numeric and boolean values
				for (k,v) in mode.items() if k != 'isPrimary')
			
			modeString = modeString.strip('_') # avoid leading/trailing _'s

		# Enforce consistent naming convention of initial caps
		if project.getProperty('enforceModeCapitalization', True):
			modeString = modeString[0].upper()+modeString[1:]

		assert modeString, 'Mode name cannot be empty'
		return modeString, mode


	def _addParameterizedTestModes(self, base):
		# base: list(TestMode)
		parameterized = self.kvDict.pop('parameterized_test_modes', None)
		if not parameterized: return base
		
		assert isinstance(parameterized, list) or isinstance(parameterized, dict), 'Parameterized test modes must be a list or dict of modes, but got: %r'%parameterized
		helper = TestModesConfigHelper(
				inheritedModes=[], 
				project=self.project, 
				testDir=os.path.dirname(self.file) if self.istest else None
				)
		return [TestMode(m.pop('mode'), isPrimary=m.pop('isPrimary', False), params=m) for m in 
			helper.createModeCombinations(
				base, 
				helper.makeAllPrimary(parameterized))]
					
	def getModes(self):
		text = self.kvDict.pop('modes', None)
		modesNode = None
		if text is None or text=='': # nb: do NOT handle [] the same as empty string since that's a common pitfall
			modesNode = self.getSingleElement('modes', optionalParents=['classification'])
			if modesNode:
				text = self.getText(modesNode)
			else: # if we have neither kvText text nor mode
				return self._addParameterizedTestModes(self.defaults.modes) # by default we inherit

		if text is None or text=='': 
			# pre-2.0 XML approach
			result = {}
			for node in modesNode.getElementsByTagName('mode'):
				modeString = node.getAttribute('mode') or self.getText(node)
				if modeString: 
					result[modeString] = {}
			
			if (modesNode.getAttribute('inherit') or 'true').lower() == 'true':
				# This logic is intended to preserve primary inherited modes; it's a bit weird, but keeping it the same for compatibility
				inherited = [x for x in self.defaults.modes if x not in result]
			else: 
				inherited = []

			result = inherited+[TestMode(k, params=v) for (k,v) in result.items()]
			if result and not any(m.isPrimary for m in result): 
				result[0] = TestMode(result[0], params=result[0].params, isPrimary=True)

			return self._addParameterizedTestModes(result)
			
		# The modern PySys 2.0+ approach with a Python eval string
		try:
			modesLambda = text
			if isinstance(modesLambda, str): # kvDict may contain non-string values direct from Python
				# use an empty namespace since if we were parsing this as real python, all import statements would be appearing later
				modesLambda = pysys.utils.safeeval.safeEval(text.strip(), extraNamespace={}, emptyNamespace=True)
			assert callable(modesLambda), 'Expecting callable (e.g. lambda helper: [...]) but got %r'%modesLambda
			helper = TestModesConfigHelper(
				# note that inheritedModes param dicts may be mutated (so good thing we'd creating a new dict here for the default modes)
				inheritedModes=[{**mode.params, **{'mode':mode, 'isPrimary':mode.isPrimary}} for mode in self.defaults.modes], 
				project=self.project, 
				testDir=os.path.dirname(self.file) if self.istest else None
				)
			modes = modesLambda(helper) # assumes it's a callable accepting a single parameter
			
			if isinstance(modes, dict):
				modes = [{**{'mode':k}, **v} for k, v in modes.items()]
			assert isinstance(modes, list), 'Expecting a list of modes, got a %s: %r'%(modes.__class__.__name__, modes)
			assert not modesNode or not modesNode.hasAttribute('inherit'), 'Cannot use the legacy inherit= attribute when using the modern Python lambda to define modes'
			

			# Add parameterized modes before validation
			modes = self._addParameterizedTestModes(modes)

			result = []
			already = set()
			expectedparams = None
			for m in modes:
				modeString, params = self.splitModeNameAndParams(m, project=self.project)
				isPrimary = params.pop('isPrimary', False)
				assert isPrimary in [True, False], 'isPrimary must be set to True or False, not %r'%isPrimary

				# Eliminate dodgy characters
				badchars = re.sub('[%s]+'%pysys.launcher.MODE_CHARS,'', modeString)
				if badchars: 
					log.debug('Unsupported characters "%s" found in test mode "%s" of %s; stripping them out', 
						''.join(set(c for c in badchars)), modeString, self.file)
					modeString = re.sub('[^%s]'%pysys.launcher.MODE_CHARS,'', modeString)

				modeString = modeString.strip().strip('_') # avoid leading/trailing _'s and whitespace, since we'll add them when composing modes
				
				assert modeString, 'Invalid mode: cannot be empty'
				assert '__' not in modeString, 'Invalid mode "%s" cannot contain double underscore'%modeString

				# Enforce consistent naming convention of initial caps
				if self.project.getProperty('enforceModeCapitalization', True):
					modeString = modeString[0].upper()+modeString[1:]
			
				assert modeString not in already, 'Duplicate mode "%s"'%modeString
				already.add(modeString)
				for p in params:
					assert not p.startswith('_'), 'Illegal mode parameter name - cannot start with underscore: %s'%p

				# check that params are the same in each one to avoid mistakes
				if expectedparams is None: expectedparams = sorted(params.keys())
				assert sorted(params.keys()) == expectedparams, f'The same mode parameter keys must be given for every mode in the list, but found {sorted(params.keys())} parameters for "{modeString}" different to {expectedparams}'

				result.append(TestMode(modeString, isPrimary=isPrimary, params=params))

			result = self._addParameterizedTestModes(result)

			# ensure there's at least one primary mode
			if result and not any(m.isPrimary for m in result): 
				result[0] = TestMode(result[0], params=result[0].params, isPrimary=True)
				
			return result

		except Exception as ex:
			log.debug('Invalid modes config: ', exc_info=True)
			raise UserError("Invalid modes configuration in %s: %s"%(self.file, ex))

				
	def getClassDetails(self):
		'''Return the Python test class attributes (name, module, searchpath), contained in the class element.'''
		classname, module = self.kvDict.pop('python_class', None), self.kvDict.pop('python_module', None)		
		
		el = self.getSingleElement('class', optionalParents=['data'])
		if el:
			classname = classname or el.getAttribute('name')
			module = module or el.getAttribute('module')
		# nb: empty means look it up in PYTHONPATH, None is a sentinel value meaning auto, based on descriptor extension
		if module == '': module = 'PYTHONPATH' # probably this is what was intended
		return [classname or self.defaults.classname, module or self.defaults.module]

	def getExecutionOrderHint(self):
		r = self.kvDict.pop('execution_order_hint', None)
		if r is None:
			e = self.getSingleElement('execution-order')

			r = None
			if e:
				r = e.getAttribute('hint')
				
		if r:
			try:
				r = float(r)
			except Exception:
				raise UserError('Invalid float value specified for execution order hint in "%s"'%self.file)
		if r is None or r == '': 
			return self.defaults.executionOrderHint
		else:
			return r


	def getUserData(self):
		
		newitems = self.kvDict.pop('user_data', {})
		if isinstance(newitems, str): 
				newitems = pysys.utils.safeeval.safeEval(newitems.strip(), 
						extraNamespace={}, emptyNamespace=True)
				
		for k in [k for k in self.kvDict if k.startswith('user_data_')]:
			newitems[k[k.find('data_')+5:]] = self.kvDict.pop(k)
		for k in [k for k in self.kvDict if k.startswith('user_data.')]: # TODO???
			newitems[k[k.find('.')+1:]] = self.kvDict.pop(k)

		if not newitems:
			data = self.getSingleElement('data')
			if data:
				for e in data.getElementsByTagName('user-data'):
					key = e.getAttribute('name').strip()
					
					# NB: we don't use inspect.cleandoc here since it'd probably slow down descriptor loading and in 99% 
					# of for multi-line strings we will be stripping whitespace anyway so not a good use of time
					value = e.getAttribute('value')
					if not value and e.childNodes:
						value = '\n'.join(n.data for n in e.childNodes 
							if (n.nodeType in {n.TEXT_NODE,n.CDATA_SECTION_NODE}) and n.data)
					if value is None: value = ''

					newitems[key] = value
		
		for key in newitems:
			assert key, 'name must be specified for user data'
			assert key not in {'input', 'output', 'reference', 'descriptor', 'runner', 'log', 'project', 'lock'}, key # prevent names that we reserve for use by the basetest/processuser

		# start with parent defaults, add children
		result = dict(self.defaults.userData)
		result.update(newitems)
		
		return result

			
	def getTestInput(self):
		value = self.kvDict.pop('input_dir', None)
		if value: return value
		
		node = self.getSingleElement('input', optionalParents=['data']) or self.getSingleElement('input-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.input
		
	def getTestOutput(self):
		value = self.kvDict.pop('output_dir', None)
		if value: return value

		node = self.getSingleElement('output', optionalParents=['data']) or self.getSingleElement('output-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.output

	def getTestReference(self):
		value = self.kvDict.pop('reference_dir', None)
		if value: return value

		node = self.getSingleElement('reference', optionalParents=['data']) or self.getSingleElement('reference-dir', optionalParents=['data'])
		if node:
			x = node.getAttribute('path') or self.getText(node)
			if x: return x
		return self.defaults.reference

	def getRequirements(self):
		'''Return a list of the requirement ids, contained in the character data of the requirement elements.'''
		reqList = [x.strip() for x in self.kvDict.pop('traceability_ids', '').split(',') if x.strip()]
		
		if self.root:
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
		if not self.root: return None
		t = u''
		if not parent: parent = self.root
		nodes = parent.getElementsByTagName(tagName)
		if len(nodes) == 0: return None
		if len(nodes) > 1: 
			raise UserError('Expected one element <%s> but found more than one in %s' % (tagName, self.file))
		if nodes[0].parentNode.tagName not in ['pysystest', 'pysysdirconfig']+optionalParents: 
				sys.stderr.write("WARNING: XML descriptor element <%s> is not permitted under <%s> of \"%s\"\n"%(tagName, nodes[0].parentNode.tagName, self.file))
				sys.stderr.flush()
		return nodes[0]

	def getElementTextOrDefault(self, tagName, default=None, parent=None, optionalParents=[]):
		"""Utility method that finds a single child element of the specified name and 
		strips leading/trailing whitespace from it. Returns an empty string if none. """
		t = u''
		node = self.getSingleElement(tagName, parent=parent, optionalParents=optionalParents)
		if node is None: return default
		return self.getText(node)

IGNORED_PYSYSTEST_SUFFIXES = tuple( (os.getenv('PYSYS_IGNORED_PYSYSTEST_SUFFIXES', '')+',~,.tmp,.bak,.swp,.orig').strip(',').replace(' ','').split(',') )
"""
A tuple listing ``pysystest.*`` suffixes that will be ignored due to being temporary/backup/swap files for common 
editors and IDEs. 

The list can be extended by setting the ``PYSYS_IGNORED_PYSYSTEST_SUFFIXES`` environment variable to a comma-separated 
list of additional extensions. 
"""

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

	This class may use multi-threading to improve performance, so any extensions 
	must be thread-safe. 
	
	:ivar pysys.config.project.Project ~.project: The `pysys.config.project.Project` instance. 
	
	"""
	def __init__(self, project, **kwargs): 
		assert project, 'project must be specified'
		self.project = project

		# Import these since they _could_ be needed when parsing pysystest.py descriptors
		import pysys.baserunner
		import pysys.basetest

		self.__descriptorPluginCache = {}
		
	def loadDescriptors(self, dir, **kwargs):
		"""Find all descriptors located under the specified directory (including its children), and 
		return them as a list.
		
		Subclasses may change the returned descriptors and/or add additional 
		instances of their own to the list after calling the super implementation::
		
		  descriptors = super().loadDescriptors(dir, **kwargs)
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
		ignoreSet = set(OSWALK_IGNORES+[DEFAULT_INPUT, DEFAULT_OUTPUT, DEFAULT_REFERENCE, "_pysys_templates"])
		
		if project.properties.get('pysysTestDescriptorFileNames') or DEFAULT_DESCRIPTOR != ['pysystest.xml']:
			# compatibility mode
			descriptorSet = set([s.strip() for s in project.getProperty('pysysTestDescriptorFileNames', default=','.join(DEFAULT_DESCRIPTOR)).split(',')])
		else:
			descriptorSet = None
		
		assert project.projectFile != None
		log = logging.getLogger('pysys.launcher')

		# although it's highly unlikely, if any test paths did slip outside the Windows 256 char limit, 
		# it would be very dangerous to skip them (which is what os.walk does unless passed a \\?\ path), 
		# so must use long-path-safe
		dir = toLongPathSafe(os.path.normpath(dir))
		assert os.path.exists(dir), dir # sanity check
		if project.projectFile:
			projectroot = toLongPathSafe(os.path.normpath(os.path.dirname(project.projectFile)))

		def fastdirname(path): 
			# This is much faster than os.path.dirname
			# The "or" is to account for minor difference fastdirname('/foo')='' whereas os.path.dirname='/'
			return path[:path.rfind(os.sep)] or '/'
		
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
			currentconfig = project._defaultDirConfig or _XMLDescriptorParser.DEFAULT_DESCRIPTOR
			for i in range(len(searchdirsuffix)): # up to but not including dir
				if i == 0:
					currentdir = projectroot
				else:
					currentdir = projectroot+os.sep+os.sep.join(searchdirsuffix[:i])
				
				if pathexists(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR):
					currentconfig = self._parseTestDescriptor(currentdir+os.sep+DIR_CONFIG_DESCRIPTOR, parentDirDefaults=currentconfig, isDirConfig=True)
					log.debug('Loaded directory configuration descriptor from %s: \n%s', currentdir, currentconfig)
			# this is the top-level directory that will be checked below
			dirconfigs[fastdirname(dir)] = currentconfig

		descriptorsToParse = []

		# NB: if changing this logic be sure to test the special case dir='/foo'
		def visitDir(root):
			with os.scandir(root) as it:
				dirs = []
				files = []
				for entry in it:
					if entry.is_dir():
						if entry.name in ignoreSet: continue
						dirs.append(entry.name)
						continue
					fname = entry.name
					if fname in ['.pysysignore', 'pysysignore']:
						log.debug('Skipping directory due to ignore file %s', entry.path)
						return
					files.append(fname)

				if dirconfigs is not None:
					parentconfig = dirconfigs[fastdirname(root)]
					assert parentconfig
					if next( (f for f in files if (f == DIR_CONFIG_DESCRIPTOR)), None):
						parentconfig = self._parseTestDescriptor(root+os.sep+DIR_CONFIG_DESCRIPTOR, parentDirDefaults=parentconfig, isDirConfig=True)
						log.debug('Loaded directory configuration descriptor from %s: \n%s', root, parentconfig)
				else:
					parentconfig = project._defaultDirConfig or _XMLDescriptorParser.DEFAULT_DESCRIPTOR

				# allow subclasses to modify descriptors list and/or avoid processing 
				# subdirectories
				if self._handleSubDirectory(root, dirs, files, descriptors, parentDirDefaults=parentconfig):
					return
				
				if descriptorSet is None: 
					intersection = [f for f in files if f.lower().startswith('pysystest.') and not f.endswith(IGNORED_PYSYSTEST_SUFFIXES)]
				else: # compatibility mode
					intersection = descriptorSet & set(files)
					
				if intersection: 
					if len(intersection) > 1: raise Exception('Only one test should be present per directory but found %s in %s'%(intersection, root))
					descriptorfile = fromLongPathSafe(root+os.sep+intersection.pop())

					descriptorsToParse.append((descriptorfile, parentconfig))
					
					# if this is a test dir, it never makes sense to look at sub directories
					return
				
				if dirconfigs is not None and len(dirs)>0:
					# stash it for when we navigate down to subdirectories
					# only add to dict if we're continuing to process children
					dirconfigs[root] = parentconfig 
				for d in dirs:
					visitDir(root+os.sep+d)

		# end of visitDir() definition
		visitDir(dir)
		
		# Tried using multithreading with Python 3.9.5 but limited benefit approx 10%, probably due to GIL
		descriptors.extend(p for p in 
				map(lambda element: self._parseTestDescriptor(descriptorfile=element[0], parentDirDefaults=element[1]),
					descriptorsToParse)
			if p)

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
		for (key, pluginCls, pluginProperties) in getattr(parentDirDefaults, '_descriptorLoaderPlugins', []):
			
			plugin = self.__descriptorPluginCache.get(key, None)
			if plugin is None:
				plugin = pluginCls()
				plugin.project = self.project
				plugin.descriptorLoader = self
				pysys.utils.misc.setInstanceVariablesFromDict(plugin, pluginProperties, errorOnMissingVariables=True)
				plugin.setup(project=self.project)

				self.__descriptorPluginCache[key] = plugin

			if plugin.addDescriptorsFromDirectory(dir=dir, subdirs=subdirs, files=files, parentDirDefaults=parentDirDefaults, descriptors=descriptors, **kwargs):
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
		assert len(kwargs)==0 or list(kwargs.keys())==['fileContents'], 'reserved for future use: %s'%kwargs.keys()
		try:
			return _XMLDescriptorParser.parse(descriptorfile, parentDirDefaults=parentDirDefaults, istest=not isDirConfig, project=self.project, **kwargs)
		except UserError:
			raise # no stack trace needed, will already include descriptorfile name
		except Exception as e:
			log.info('Failed to read descriptor %s: ', descriptorfile, exc_info=True)
			raise Exception("Error reading descriptor from '%s': %s - %s" % (descriptorfile, e.__class__.__name__, e)) from e

