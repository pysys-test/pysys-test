#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B.Grieve

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


# This set of imports was copied from BaseTest (minus a little tidying up, e.g. removing BaseTest-specific dependencies) 
# to preserve compatibility with 1.5.0 PySys tests using assertEval, before we started controlling the environment used 
# for eval more carefully. 

# It still contains lots of symbols which are likely to be useful when performing an eval such as IS_WINDOWS, etc

import os.path, time, threading, logging, sys
import re
import math
import json

from pysys import log
from pysys.constants import *
from pysys.exceptions import *

from pysys.utils.pycompat import *
from pysys.utils.fileutils import pathexists
import pysys

import importlib
from importlib import import_module

def safe_eval(expr, extraNamespace={}):
	"""
	Executes eval(...) on the specified string expression, using a controlled globals()/locals() environment to 
	ensure we do not break compatibility between PySys versions, and that a sensible set of PySys constants and 
	modules are available. 
	
	The global environment used for evaluation includes the ``os.path``, ``math``, ``sys``, ``re``, ``json``, and ``locale`` 
	standard Python modules, as well as the ``pysys`` module and the contents of the `pysys.constants` module, e.g. ``IS_WINDOWS``. 
	
	If necessary, symbols for additional modules can be imported dynamically using ``import_module``, e.g. 
	``safe_eval("import_module('difflib').get_close_matches('app', ['apple', 'orange', 'applic']")``.
	
	:param expr: The string to be evaluated.
	
	:param extraNamespace: A dict of string names and Python object values to be included in the globals dict 
		used to evaluate this string. 
	"""
	env = globals()
	if extraNamespace:
		env = dict(env)
		for k,v in extraNamespace.items():
			env[k] = v
	return eval(expr, env)
	