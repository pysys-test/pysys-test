"""
Sphinx extension that automatically and recursively generates .rst files containing autodoc/autosummary 
directives for a hierarchy of Python modules. 

See https://github.com/ben-spiller/sphinx-autodocgen
"""

__copyright__ = "Copyright (C) 2019-present Ben Spiller"
__author__ = "Ben Spiller"
__license__ = "MIT"
__version__ = "1.4.dev"

__all__ = ['AutoDocGen', 'setup']


import os
import sys
from typing import List, Dict, Tuple
import inspect
import importlib
import pkgutil
import re
import traceback

from sphinx.util import logging
from sphinx.util import rst

import sphinx.ext.autosummary
import sphinx.ext.autodoc
import sphinx.environment
from sphinx.pycode import ModuleAnalyzer

logger = logging.getLogger(__name__)

# TODO: convert these to config options; maybe add one for groups of items
member_underline = '=' # maybe call it member name underline (and if blank, don't include one)
module_underline = '~'

doc_module_member_types = ['module', 'data', 'class', 'exception', 'function'] # these names each correspond to autoXXX directives; order matters; module means submodule
# TODO: could be a dict where value is: autosummary, automember_grouped_by_type, automember_ungrouped
autosummary_member_types = ['module'] # type for which we'll generate an autosummary (implies no members are shown!) instead of an autodoc


class AutoDocGen:
	# NB: To avoid warnings with modern Sphinx versions, all items in the config should be pickable (i.e. no modules, callables etc)
	class Config: 
		"""Configuration options for this extension. 
		
		These must be added to a dictionary ``autodocgen_config = [{...}]`` in your ``conf.py`` file. 
		"""
		
		modules: List[str] = []
		"""The list of modules for which autodoc is to be recursively generated. 
		
		It is recommended to use strings, but for backwards compatibility you want to pass the module objects directly 
		(deprecated, and will give warnings with modern Sphinx versions), you will need to add an import statement in your 
		``conf.py`` before you can reference them here.
		"""
		
		generated_source_dir: str='autodocgen/'
		""" The directory in which generated rst files will be written. 
		This must be a location under the documentation source dir. """

		overwrite_generated_source_rsts: bool=True
		""" By default any existing .rst files are overwritten at the start of the build. 
		
		Set this to false to skip overwriting of rst files that already exist, allowing you to selectively overwrite 
		parts of the generated output with a custom file. 
		
		This option can only be used if you take steps to explicitly clean stale files from previous builds, or use a pristine directory 
		each time.
		"""
		# TODO: if we saved a list of generated rst from last time, we could clean them up then set this to False by default to get faster incremental builds

		skip_module_regex: str='.+[.]_.*'
		""" If a module matches this then it and any of its submodules will be skipped. 
		
		By default we skip names that begin with a single underscore. """

		skip_on_docstring_regex: str=':meta private:'
		""" If a member or module's docstring contains this regular expression then it will be skipped. 
		
		This regex works on attribute docstrings (which Sphinx supports, even though Python's ``__doc__`` does not 
		work for attributes), so is more robust than checking ``__doc__`` from the ``autodoc-skip-member`` hook. 
		
		By default we skip if the docstring contains the special directive (defined by this extension) 
		``:meta private: REASON HERE``. 
		"""
		# uses same syntax as the official autodoc feature; it might therefore not be necessary anymore

		module_title_decider: dict[str,str] = {}
		"""
		A dictionary that allows overriding the title displayed in the table of contents for specified module names. 

		For backwards compatibility this can also be a function (modulename->title) but that is deprecated since it produces warnings with latest sphinx. 
		"""

		autodoc_options_decider: dict[str,dict[str,str]] = {}
		"""
		A dict whose key is fullname of each module, and value is a dict of autodoc options to use for documenting the specified item, 
		similar to the autodoc ``autodoc_default_options`` configuration option. 
		
		For example this could be used to enable autodoc flags such as 'private-members' by returning 
		{'private-members':True} for some names and not others. 
		
		For backwards compatibility - but deprecated - you can provide a callable here with signature
		`(app, what, fullname, obj, docstring, defaultOptions, extra: defaultOptions)` to dynamically return 
		the required options dir (or `defaultOptions` to use the defaults). However this is not pickable it produces 
		a warning with modern Sphinx versions so is not recommended. 
		"""

		write_documented_items_output_file: str = None
		"""A diagnostic option that writes a sorted list of all documented modules and (direct) members to a text 
		file. This allows before/after diffing of documented members after you make changes. It could be compared by a 
		test to a reference file, to ensure you don't add items to the documented public API without noticing. """

		_config_keys = ['modules', 'generated_source_dir', 'skip_module_regex', 'skip_on_docstring_regex', 
			'autodoc_options_decider', 'write_documented_items_output_file', 'module_title_decider', 'overwrite_generated_source_rsts']

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

		self.app.add_config_value('autodocgen_config', default=[], rebuild='env')

		# must generate and update the generated rst files quite early in the process (before builder stage)
		self.app.connect('config-inited', lambda app, config: self.generateAll())

	def generateAll(self):
		# allow a list of generation configs
		config = self.app.config.autodocgen_config

		if isinstance(config, dict): config = [config]
		for c in config:
			self.config = dict(c)
			self.generate()

	def generate(self):
		"""
		Visits the configured modules and generates .rst files for them. 
		
		Called on the Sphinx builder-inited event. 
		"""
		for k in self.Config._config_keys:
			self.config.setdefault(k, getattr(self.Config, k))
		
		if isinstance(self.config['autodoc_options_decider'], dict):
			optionsdict = self.config['autodoc_options_decider']
			self.config['autodoc_options_decider'] = lambda app, what, fullname, obj, docstring, defaultOptions, extra: (
				optionsdict[fullname] if fullname in optionsdict else defaultOptions)
		
		modules = self.config['modules']
		generated_dir = self.config['generated_source_dir']
		assert os.path.normpath(generated_dir) != os.path.normpath('.'), 'Cannot use current path as generated_source_dir - everything would be wiped out!'  

		if not modules: 
			assert False, 'no modules'
			return

		os.makedirs(generated_dir, exist_ok=True)
		# we must delete any extra files from previous runs that are left around, otherwise we may get invalid results; 
		# but don't delete files we've just created
		self.rst_files_generated = set()
		self.documented_items = set() # list of names of everything we've documented, which can be used for diff-ing output
		
		for mod in modules:
			if isinstance(mod, str):
				# if a string, import the module
				try:
					mod = importlib.import_module(mod)
				except ImportError as e:
					logger.error(f'Error importing module listed in autodocgen_config "{mod}": {e}')
					raise
			self.visit_module(mod)
		
		for f in set(os.listdir(generated_dir)) - self.rst_files_generated:
			os.remove(generated_dir+'/'+f)
		
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
		
		defaults = {'members':bool(memberType in {'class', 'exception'})} # could get this from the autodoc default instead?
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
		
		:return: A string, or None if there is to be no dedicated section for this member type (e.g. if you want 
		the members to be listed in source order) rather than grouped by type. (TODO: make that possible)
		
		"""
		
		for mname, m, _ in members:
			self.documented_items.add(f'{mname} ({memberType})')
		
		# special case, for modules an autosummary works best for seeing at a glance what's in each module
		if memberType in autosummary_member_types:
			# Do we need a title here? maybe a generic way to specify titles for each member type. Perhaps just an option?
			# Would we need to separately generate an rst for each of these if we use an autosummary; maybe best to not make this a user config option
			return '\n'.join([
				".. autosummary::", 
				"  :toctree: ./", 
				""]+[
				f'  {name.replace(module.__name__+".", "")}' for (name,_, _) in members])

		return '\n'.join(self.get_module_member_rst(memberType, mname, m, docstring) for (mname,m, docstring) in members)

	def generate_module_rst(self, module, membersByType: Dict[str, List[Tuple[str,object,str]]]):
		"""
		Generates the RST for a Python module. 
		
		:param membersByType: The filtered set of members to be documented, keyed by member type. 
		"""
		if not membersByType: return None

		module_fullname = module.__name__

		self.documented_items.add(f'{module_fullname} (module)')

		if callable(self.config['module_title_decider']):
			# deprecated, but still supported for backwards compatibility
			title = self.config['module_title_decider'](module_fullname)
		else:
			# modern way to specify title overrides
			title = self.config['module_title_decider'].get(module_fullname, module_fullname)

		output = """
{module_title}
{module_title_underline}

.. automodule:: {module_fullname}

.. currentmodule:: {module_fullname}

""".format(module_fullname=module_fullname, module_title=rst.escape(title), 
		module_title_underline=module_underline*len(rst.escape(title)))

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
		skipped = self.config['skip_module_regex'] and re.match(self.config['skip_module_regex'], modulename)

		skip_on_docstring_regex = self.config['skip_on_docstring_regex']
		if skip_on_docstring_regex:
			if mod.__doc__ and re.search(skip_on_docstring_regex, mod.__doc__): skipped=True

		logger.info(f'{self} Visiting module: {modulename} {"(skipped)" if skipped else ""}')
		if skipped: 
			return False
		# TODO: would be nice to call the autodoc skip function here too
		
		# could use a flat structure for the global modules list if we're not documenting submodules, e.g.:
		#    if 'module' not in doc_module_member_types: allmodules.append(modulename) # TODO: do something with this
		
		# can't use getmembers for getting submodules of packages
		membersByType = {t:[] for t in doc_module_member_types}

		if hasattr(mod, '__path__'): # if this is a package (i.e. contains other modules)
			for _, submodulename, _ in pkgutil.iter_modules(mod.__path__, prefix=modulename+ '.'):
				submodule = importlib.import_module(submodulename.lstrip('.'))
				if not self.visit_module(submodule): continue
				if 'module' in membersByType: membersByType['module'].append( (submodulename, submodule, submodule.__doc__))
				
		# It'd be possible to iterate over mod.__dict__.items() but there are some subtlies around how to decide 
		# what to document (including the __all__ handling in get_object_members and the fact that we have to use the 
		# Sphinx ModuleAnalyzer if we want to get docstrings for attributes which filter_members does), 
		# .... which we can avoid reimplementing by just using the existing code. 
		# This was implemented against Sphinx 2.2.0

		try:
			# unfortunately the FakeDirective from autosummary is a bit too fake to actually work, so make it slightly less so
			directive = sphinx.ext.autosummary.FakeDirective()
			if not hasattr(self.app, 'project'): self.app.project = None
			directive.env = sphinx.environment.BuildEnvironment(self.app)
			
			documenterclass = sphinx.ext.autosummary.get_documenter(app=self.app, obj=module, parent=None)
			documenter = documenterclass(directive, modulename)
			
			if not documenter.parse_name() or not documenter.import_object():
				assert False, 'documenter failed to import module %s'%module
			
			# must call this before filter_members will work correctly
			documenter.analyzer = ModuleAnalyzer.for_module(modulename)
			attr_docs = documenter.analyzer.find_attr_docs()

			# find out which members are documentable; use __dict__.items() to retain the ordering info, but delegate to 
			# autodoc get_object_members for its __all__ handling logic
			_, objectMembers = documenter.get_object_members(want_all=True) # list[ObjectMember]

			# key is the list of member names (from autosummary), value is whether it's marked as skipped by autosummary
			permittedmembers = {
				memberinfo.__name__ if hasattr(memberinfo, '__name__') else memberinfo[0] # fallback to tuple for ancient sphinx versions
				: getattr(memberinfo, 'skipped', False)
				for memberinfo in objectMembers
				}
			
			if hasattr(sphinx.ext.autodoc, 'ObjectMember'):
				def createObjectMember(mname, m, skipped): return sphinx.ext.autodoc.ObjectMember(mname, m, skipped=skipped)
			else:
				def createObjectMember(mname, m, skipped): tuple([mname, m]) # tuple for old Sphinx versions; skipped is handled differently
			members = [createObjectMember(mname,m,permittedmembers[mname]) for mname, m in mod.__dict__.items() if mname in permittedmembers]
		
			# TODO: could implement ordering c.f. autodoc_member_order
			for (mname, m, isattr) in documenter.filter_members(members, want_all=True):
				logger.debug('   visiting member: %s'%mname)
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
				logger.info(f'{self} No .rst generated for {modulename}')
				return

			rstfile = self.config['generated_source_dir']+f'/{mod.__name__}.rst'
			self.rst_files_generated.add(os.path.basename(rstfile))
			
			if os.path.exists(rstfile):
				with open(rstfile, 'r', encoding='utf-8') as f:
					if f.read() == rst:
						return True # nothing to do

				if not self.config['overwrite_generated_source_rsts']:
					logger.info(f'{self}    Skipping overwrite of {mod.__name__}.rst due to overwrite_generated_source_rsts=True')
					return True

			with open(rstfile, 'w', encoding='utf-8') as f:
				f.write(rst)
			
			return True # indicates this module isn't skipped
		except Exception as e: # since sphinx doesn't print the stack trace, print it ourselves so we can see where it really went wrong
			logger.error(f'Error analyzing module {modulename}: {traceback.format_exc()}')
			raise

def setup(app):
	AutoDocGen(app).connect()
	return {'version': __version__}

