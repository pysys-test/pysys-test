#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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



import sys, imp

def import_module(name, path, reload=False):
	"""Import a named module, searching within a list of paths.
	
	Supports loading of hierarchical modules from a list of paths, returning a reference to the loaded module. 
	Reloading of the module can be requested should the module already exist in sys.modules. Note that in a 
	module named X.Y.Z, should reload be set to True only the tail module, X.Y.Z, will be reloaded on import; 
	the intervening modules, X and X.Y, will not be reloaded. 
	
	@param name: The module name
	@param path: A list of paths to search for the module
	@param reload: A boolean indicating if the module should be reloaded if already in sys.modules
	
	"""
	elements = name.split(".")
	module = __import_module(elements[0], elements[0], None, path, reload and elements[0] == name)
	if not module: raise ImportError("No module named " + name)

	if len(elements) > 1:  
		for element in elements[1:]:
			fqname = "%s.%s" % (module.__name__, element)
			module = __import_module(fqname, element, module, module and module.__path__, reload and fqname == name)
			if not module: raise ImportError("No module named " + fqname)
	return module


def __import_module(fqname, qname, parent, path, reload):
	"""Method to load a module.

	@param fqname: The fully qualified name of the module
	@param qname: The qualified name relative to the parent module (if one exists)
	@param parent: A reference to the loaded parent module
	@param path: The path used to search for the module
	@param reload: Boolean indicating if the module should be reloaded if already in sys.modules
	
	"""
	if not reload:
		try:
			return sys.modules[fqname]
		except KeyError:
			pass
	try:
		file, pathname, description = imp.find_module(qname, path)
	except ImportError:
		return None
	try:
		module = imp.load_module(fqname, file, pathname, description)
	finally:
		if file: file.close()
	if parent: setattr(parent, qname, module)
	return module


