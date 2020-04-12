"""
Sphinx extension that automatically and recursively generates .rst files containing autodoc/autosummary 
directives for a hierarchy of Python modules. 
"""

__copyright__ = "Copyright (C) 2019 Ben Spiller"
__author__ = "Ben Spiller"
__license__ = "Apache 2.0"
__version__ = "1.0.dev"

__all__ = ['AutoDocGen', 'setup']


import os
import sys
from typing import List, Dict, Tuple
import inspect
import importlib
import pkgutil
import re

from sphinx.util import logging
from sphinx.util import rst

import sphinx.ext.autosummary
from sphinx.pycode import ModuleAnalyzer, PycodeError

logger = logging.getLogger(__name__)

# TODO: convert these to config options; maybe add one for groups of items
member_underline = '=' # maybe call it member name underline (and if blank, don't include one)
module_underline = '~'

doc_module_member_types = ['module', 'data', 'class', 'exception', 'function'] # these names each correspond to autoXXX directives; order matters; module means submodule
# TODO: could be a dict where value is: autosummary, automember_grouped_by_type, automember_ungrouped
autosummary_member_types = ['module'] # type for which we'll generate an autosummary (implies no members are shown!) instead of an autodoc


class AutoDocGen:
	class Config: 
		"""Configuration options for this extension. 
		
		These must be added to a dictionary ``autodocgen_config = {...}`` in your ``conf.py`` file. 
		"""
		
		modules: List[object] = []
		"""The list of modules for which autodoc is to be recursively generated. 
		
		These are imported module objects (not strings), so you will need to add an import statement in your 
		``conf.py`` before you can reference them here.
		"""
		
		generated_source_dir: str='autodocgen/'
		""" The directory in which generated rst files will be written. 
		This must be a location under the documentation source dir. """

		skip_module_regex: str='.+[.]_.*'
		""" If a module matches this then it and any of its submodules will be skipped. 
		
		By default we skip names that begin with a single underscore. """

		skip_on_docstring_regex: str='.. private::'
		""" If a member or module's docstring contains this regular expression then it will be skipped. 
		
		This regex works on attribute docstrings (which Sphinx supports, even though Python's ``__doc__`` does not 
		work for attributes), so is more robust than checking ``__doc__`` from the ``autodoc-skip-member`` hook. 
		
		By default we skip if the docstring contains the special directive (defined by this extension) 
		``.. private:: REASON HERE``. 
		"""

		autodoc_options_decider = lambda app, what, fullname, obj, docstring, defaultOptions, extra: defaultOptions
		"""
		A callback function that returns a dict of the autodoc options to use for documenting the specified item, 
		similar to the autodoc ``autodoc_default_options`` configuration option. 
		
		For example this could be used to enable autodoc flags such as 'private-members' by returning 
		{'private-members':True} for some names and not others. Return defaultOptions to use the defaults. 
		
		Alternatively, for simple cases just set this to a dict whose key is fullname and value is the desired options 
		dict. 
		"""

		write_documented_items_output_file: str = None
		"""A diagnostic option that writes a sorted list of all documented modules and (direct) members to a text 
		file. This allows before/after diffing of documented members after you make changes. It could be compared by a 
		test to a reference file, to ensure you don't add items to the documented public API without noticing. """

		_config_keys = ['modules', 'generated_source_dir', 'skip_module_regex', 'skip_on_docstring_regex', 
			'autodoc_options_decider', 'write_documented_items_output_file']

	def __init__(self, app):
		"""
		Sphinx extension that automatically and recursively generates .rst files containing autodoc/autosummary 
		directives for one or more Python modules. 
		
		This class has been designed to be easy to adapt to different purposes by means of subclassing. This should 
		provide additional customization power that would not be available from string templates. 
		
		The constructor sets up required configuration values, but connection to the ``app`` happens only in 
		`connect()`, so you can invoke its methods from your own extension if desired. 
		
		:param app: the Sphinx object from the ``conf.py``'s ``setup()`` method. 
		"""
		self.app = app

	def __str__(self): return '<AutoDocGen>' # for logging

	def connect(self):
		"""
		Connects this Sphinx extension to the ``app`` instance specified in the constructor. 
		"""
		# dependencies
		self.app.setup_extension('sphinx.ext.autodoc')
		self.app.setup_extension('sphinx.ext.autosummary')

		self.app.add_config_value('autodocgen_config', default={}, rebuild='env')

		# must generate and update the generated rst files quite early in the process (before builder stage)
		self.app.connect('config-inited', lambda app, config: self.generate())

	def clean(self):
		# delete any existing files generated by this to ensure a clean run
		generated_dir = self.config['generated_source_dir']
		if not os.path.exists(generated_dir): return
		for f in os.listdir(generated_dir): 
			os.remove(generated_dir+'/'+f)
			
	def generate(self):
		"""
		Visits the configured modules and generates .rst files for them. 
		
		Called on the Sphinx builder-inited event. 
		"""
		self.config = dict(self.app.config.autodocgen_config)
		for k in self.Config._config_keys:
			self.config.setdefault(k, getattr(self.Config, k))
		
		if isinstance(self.config['autodoc_options_decider'], dict):
			optionsdict = self.config['autodoc_options_decider']
			self.config['autodoc_options_decider'] = lambda app, what, fullname, obj, docstring, defaultOptions, extra: (
				optionsdict[fullname] if fullname in optionsdict else defaultOptions)
		
		modules = self.config['modules']
		generated_dir = self.config['generated_source_dir']
		assert os.path.normpath(generated_dir) != os.path.normpath('.'), 'Cannot use current path as generated_source_dir - everything would be wiped out!'  
		
		self.clean()

		if not modules: 
			assert False, 'no modules'
			return

		os.makedirs(generated_dir, exist_ok=True)
		
		self.documented_items = set() # list of names of everything we've documented, which can be used for diff-ing output
		
		for mod in modules:
			self.visit_module(mod)
		
		if self.config['write_documented_items_output_file']:
			with open(os.path.join(self.config['generated_source_dir'], self.config['write_documented_items_output_file']), 'w', encoding='utf-8') as f:
				items = list(self.documented_items)
				items.sort()
				for m in items:
					f.write(f'{m}\n')

	def get_module_member_rst(self, memberType, qualifiedName, obj, docstring):
		name = qualifiedName.split('.')[-1]
		result = """
{name_escaped}
{name_underline}

.. auto{type}:: {name}
""".format(
			qualified_name=qualifiedName,
			name=name,
			name_escaped=rst.escape(name),
			name_underline=member_underline*len(rst.escape(name)),
			type=memberType
		)
		
		defaults = {'members':bool(memberType in {'class', 'exception'})} # TODO: could get this from the autodoc default
		autodocoptions = self.config['autodoc_options_decider'](self.app, memberType, qualifiedName, obj, docstring, defaults, None)

		if autodocoptions is None: autodocoptions = defaults
		for k, v in autodocoptions.items():
			if v is False: continue
			result +=f'   :{k}:'
			if not (v is None or v is True):
				result += ' '+v
			result += '\n'
		
		return result

	def generate_member_type_rst(self, module, memberType: str, members: List[Tuple[str,object,str]]):
		"""Generate RST for members of a specified type. 
		
		@returns: A string, or None if there is to be no dedicated section for this member type (e.g. if you want 
		the members to be listed in source order) rather than grouped by type. (TODO: make that possible)
		
		"""
		
		for mname, m, _ in members:
			self.documented_items.add(f'{mname} ({memberType})')
		
		# special case, for modules an autosummary works best for seeing at a glance what's in each module
		if memberType in autosummary_member_types:
			# TODO: do we need a title here? maybe a generic way to specify titles for each member type. Perhaps just an option?
			# TODO: would we need to separately generate an rst for each of these if we use an autosummary; maybe best to not make this a user config option
			return '\n'.join([
				".. autosummary::", 
				"  :toctree: ./", 
				""]+[
				f'  {name}' for (name,_, _) in members])

		return '\n'.join(self.get_module_member_rst(memberType, mname, m, docstring) for (mname,m, docstring) in members)

	def generate_module_rst(self, module, membersByType: Dict[str, List[Tuple[str,object,str]]]):
		"""
		Generates the RST for a Python module. 
		
		@param membersByType: The filtered set of members to be documented, keyed by member type. 
		"""
		if not membersByType: return None

		module_fullname = module.__name__

		self.documented_items.add(f'{module_fullname} (module)')

		output = """
{module_fullname}
{module_fullname_underline}

.. automodule:: {module_fullname}

.. currentmodule:: {module_fullname}

""".format(module_fullname=rst.escape(module_fullname), module_fullname_underline=module_underline*len(rst.escape(module_fullname)))

		for memberType, members in membersByType.items():
			if not members: continue # don't show empty sections

			extra = self.generate_member_type_rst(module, memberType, members)
			
			if extra: output += '\n'+extra	
		return output
		
	def visit_module(self, module) -> bool:
		"""
		Visit the specified module and generate doc for it, and if it is a package module also any submodules.
		
		Does nothing if the specified module has been skipped. 
		
		:param module: The module object. 
		"""
		mod=module
		modulename = mod.__name__
		logger.info(f'{self} Visiting module: {modulename}')
		if self.config['skip_module_regex'] and re.match(self.config['skip_module_regex'], modulename): return False
		# TODO: call skip here too
		# TODO: skip undoc'd modules?
		
		# use a flat structure for the global modules list if we're not documenting submodules
		#TODO: if 'module' not in doc_module_member_types: allmodules.append(modulename) # TODO: do something with this
		
		# can't use getmembers for getting submodules of packages
		membersByType = {t:[] for t in doc_module_member_types}

		if hasattr(mod, '__path__'): # if this is a package (i.e. contains other modules)
			for _, submodulename, _ in pkgutil.iter_modules(mod.__path__, prefix=modulename+ '.'):
				submodule = importlib.import_module(submodulename.lstrip('.'))
				if not self.visit_module(submodule): continue
				if 'module' in membersByType: membersByType['module'].append( (submodulename, submodule, submodule.__doc__))
				
		moduleall = set(getattr(mod, '__all__', []))

		# It'd be possible to iterate over mod.__dict__.items() but there are some subtlies around how to decide 
		# what to document (including the __all__ handling in get_object_members and the fact that we have to use the 
		# Sphinx ModuleAnalyzer if we want to get docstrings for attributes which filter_members does), 
		# .... which we can avoid reimplementing by just using the existing code. 
		# This was implemented against Sphinx 2.2.0

		# unfortunately the FakeDirective from autosummary is a bit too fake to actually work, so make it slightly less so
		class FakeBuildEnvironment(object): 
			def __init__(self, app): self.app, self.config = app, app.config	
		directive = sphinx.ext.autosummary.FakeDirective()
		directive.env = FakeBuildEnvironment(self.app)
		
		documenterclass = sphinx.ext.autosummary.get_documenter(app=self.app, obj=module, parent=None)
		documenter = documenterclass(directive, modulename)
		
		if not documenter.parse_name() or not documenter.import_object():
			assert False, 'documenter failed to import module %s'%module
		
		# must call this before filter_members will work correctly
		documenter.analyzer = ModuleAnalyzer.for_module(modulename)
		attr_docs = documenter.analyzer.find_attr_docs()

		# find out which members are documentable; use __dict__.items() to retain the ordering info, but delegate to 
		# autodoc get_object_members for its __all__ handling logic
		permittedmembers = set(memberinfo[0] for memberinfo in documenter.get_object_members(want_all=True)[1])
		members = [(mname,m) for mname, m in mod.__dict__.items() if mname in permittedmembers]
		
		skip_on_docstring_regex = self.config['skip_on_docstring_regex']

		# TODO: ordering c.f. autodoc_member_order
		for (mname, m, isattr) in documenter.filter_members(members, want_all=True):
			if not isattr and not self.app.config['autodoc_default_options'].get('imported-members',False) and getattr(m, '__module__', modulename) != modulename: 
				# need to immediately rule out the majority of items which aren't really defined in this module; 
				# data attributes don't have module set on them so don't do the check for those else we'd miss stuff that 
				# should be included
				continue
			
			if isattr:
				mtype = 'data'
			elif inspect.isclass(m):
				if isinstance(m, BaseException):
					mtype = 'exception'
				else:
					mtype = 'class'
			elif inspect.ismodule(m):
				continue # submodules are handled above, so anything here will be an imported module that we don't want
			elif inspect.isfunction(m):
				mtype = 'function'
			else:
				logger.debug(f'Ignoring unknown member type: {mname} {repr(m)}')
				continue

			if ('', mname) in attr_docs:
				docstring = '\n'.join(attr_docs[('', mname)])
			else:
				docstring = getattr(m, '__doc__', None)
			if skip_on_docstring_regex:
				if docstring and re.search(skip_on_docstring_regex, docstring):
					logger.info(f'{self} Skipping {modulename}.{mname} due to its docstring matching the skip_on_docstring_regex')
					continue

			membersByType[mtype].append((modulename+'.'+mname, m, docstring))

		logger.debug('%s Visiting module %s with members: %s', self, modulename, membersByType)

		rst = self.generate_module_rst(mod, membersByType)
		if not rst: 
			logger.info(f'{self} No RST generated for {modulename}')
			return

		with open(self.config['generated_source_dir']+f'/{mod.__name__}.rst', 'w', encoding='utf-8') as f:
			f.write(rst)
		
		return True # indicates this module isn't skipped

def setup(app):
	AutoDocGen(app).connect()
	return {'version': __version__}

