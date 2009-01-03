#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

import sys, imp, threading

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
	if not module: raise ImportError, "No module named " + name

	if len(elements) > 1:  
		for element in elements[1:]:
			fqname = "%s.%s" % (module.__name__, element)
			module = __import_module(fqname, element, module, module and module.__path__, reload and fqname == name)
			if not module: raise ImportError, "No module named " + fqname
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


