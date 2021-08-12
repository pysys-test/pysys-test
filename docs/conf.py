# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import shutil
from typing import List, Dict, Tuple

DOC_SOURCE_DIR = os.path.dirname(__file__)
PYSYS_ROOT_DIR = os.path.abspath(DOC_SOURCE_DIR+'/..')

sys.path.append(PYSYS_ROOT_DIR)

# Need to create dynamically generated rst files which we'll be including in the package
sys.path.append(PYSYS_ROOT_DIR+'/docs')
import create_templated_rsts
create_templated_rsts.prepareDocBuild()

# -- Project information -----------------------------------------------------

from datetime import date
copyright = f'2006-{date.today().year} M.B. Grieve; documentation last updated on {date.today().strftime("%Y-%m-%d")}'
author = 'M.B. Grieve and Ben Spiller'

# The full version, including alpha/beta/rc tags
with open(PYSYS_ROOT_DIR+'/VERSION', encoding='ascii') as versionfile:
	pysys_release = versionfile.read().strip()

project = f'PySys v{pysys_release}'

# -- General configuration ---------------------------------------------------

sys.path.append(DOC_SOURCE_DIR+'/ext') # temporary measure to get sphinx_autodocgen

assert os.path.exists(DOC_SOURCE_DIR+'/ProjectConfiguration.rst'), 'must run setup.py first, to generate docs/ProjectConfig.rst'

# To refer to another .rst document use                  :doc:`TestDescriptors`
# To refer to a section inside another .rst document use :ref:`TestDescriptors:Sample pysysdirconfig.xml`

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
	'sphinx_epytext',
	'sphinx_autodocgen',
]

default_role = 'py:obj' # So that `xxx` is converted to a Python reference. Use ``xxx`` for monospaced non-links.

autosectionlabel_prefix_document = True

autoclass_content = 'both' # include __init__ params in doc strings for class

autodoc_inherit_docstrings = False

autodoc_member_order = 'bysource' # bysource is usually a more logical order than alphabetical

autodoc_default_options = {
	'show-inheritance':True, # show base classes
    #'members': 'var1, var2',
    #'member-order': 'bysource',
    #'special-members': '__init__',
    #'undoc-members': True,
    # The supported options are 'members', 'member-order', 'undoc-members', 'private-members', 'special-members', 'inherited-members', 'show-inheritance', 'ignore-module-all', 'imported-members' and 'exclude-members'.
    #'exclude-members': '__weakref__'
}

#nitpicky = True # so we get warnings about broken links

from sphinx.util import logging
logger = logging.getLogger('conf.py')

def autodoc_skip_member(app, what, name, obj, skip, options):
	# nb: 'what' means the parent that the "name" item is in e.g. 'class', 'module'

	# in case we ever need to customize skipping behaviour; not currently used
	if skip: 
		# we don't want to hide protected class methods with a single underscore; but we do want to hide any 
		# that include a double-underscore since _classname__membername is how Python mangles private members
		if (name.startswith('_') and ('__' not in name) and what=='class' and callable(obj) 
				and obj.__doc__ and ':meta private:' not in obj.__doc__):
			logger.info(f'conf.py: UNSKIPPING protected class method: {name}')
			return False
		logger.debug(f'conf.py: ALREADY Skipping member: {name}')
		return None
		
	return None

autosummary_generate = True
autosummary_generate_overwrite = False

import pysys.basetest
autodocgen_config = {
	'modules':[pysys], 
	'generated_source_dir': DOC_SOURCE_DIR+'/autodocgen/',
	'skip_module_regex': '(.*[.]__|pysys.basetest)', # if module matches this then it and any of its submodules will be skipped
	'write_documented_items_output_file': PYSYS_ROOT_DIR+'/docs/build_output/autodocgen_documented_items.txt',
	'autodoc_options_decider': { # for usability, it's best to fold the inherited ProcessUser content into BaseTest/BaseRunner
		'pysys.basetest.BaseTest':    { 'inherited-members':True },
		'pysys.baserunner.BaseRunner':{ 'inherited-members':True },
	},
	'module_title_decider': lambda modulename: 'API Reference' if modulename=='pysys' else modulename,
}

def setup(app):
	app.connect("autodoc-skip-member", autodoc_skip_member)

	def supportGitHubPages(app, exception):
		outputdir = os.path.abspath('docs/build_output/html')
		open(outputdir+'/.nojekyll', 'wb').close()
	app.connect('build-finished', supportGitHubPages)


# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme' # read-the-docs theme looks better than the default "classic" one but has bugs e.g. no table wrapping

html_theme_options = {
	'display_version': True,
	#'prev_next_buttons_location': 'bottom',
	#'style_external_links': False,
	#'vcs_pageview_mode': '',
	#'style_nav_header_background': 'white',
	# Toc options
	'collapse_navigation': True,
	'sticky_navigation': True,
	#'navigation_depth': 4,
	'includehidden': False,
	#'titles_only': False
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

html_context = {'css_files': [
	# Workaround for RTD 0.4.3 bug https://github.com/readthedocs/sphinx_rtd_theme/issues/117
	'_static/theme_overrides.css',  # override wide tables in RTD theme
]}
