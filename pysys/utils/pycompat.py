#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B.Grieve

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
Compatibility utilities for older Python versions. 

This module is now deprecated as all functionality can be provided by the Python standard library. 

Instead of ``quotestring`` use `pysys.utils.misc.quoteString`. 
"""

import sys, os, io, locale
import copy
import logging
__log = logging.getLogger('pysys.pycompat')

PY2 = sys.version_info[0] == 2

string_types = (str,)

binary_type = bytes

def isstring(s): 
	""" Returns True if the specified object is a python string. 
	
	Deprecated - use ``isinstance(s, str)`` instead.
	
	"""
	return isinstance(s, str)

def quotestring(s):
	""" Adds double quotation marks around the specified character or byte string, 
	and additional escaping only if needed to make the meaning clear, but trying to 
	avoid double-slashes unless actually needed since it makes paths harder to read
	
	If a byte string is provided then the 
	``repr()`` representation is used instead. 
	
	Deprecated - use `pysys.utils.misc.quoteString` instead. 
	
	"""
	# this function exists primarily to provide the same quoting behaviour 
	# for str/unicode in Python 2 and str in Python 3, but avoiding 
	# the confusing "b'valuehere'" representation that "%s" would 
	# produce for python 3 bytes objects
	r = repr(s)
	if not isstring(s): return r
	
	if '\\' in r.replace('\\\\',''): # if it contains escape sequences like \n to \" we'd better just use repr so it's unambiguous
		return r
	
	# repr uses single quotes, so using double quotes is a good way to make it distinguishable 
	# (the other option would be using r'...' since essentially this is like a Python raw string

	return '"%s"'%s
	
def openfile(path, mode='r', encoding=None, errors=None, **kwargs):
	"""
	Opens the specified file, following the default 
	"open()" semantics for this Python version unless an encoding is 
	explicitly specified, in which case a file stream 
	yielding (unicode) character strings is always returned. 
	
	This method returns a file stream yielding character strings 
	unless a binary mode was specified in which case a stream yielding 
	bytes is returned. 
	
	Deprecated - use ``io.open(pysys.utils.fileutils.toLongPathSafe(path), ...)`` instead. 
	
	:param path: The path to open; must be an absolute path. 
		Even on Windows this path can be long (e.g. more than the usual 256 
		character Windows limit). 
	
	:param mode: The file mode, e.g. 'r' for reading, 'wb' for binary writing. 
	
	:param encoding: The encoding to use to translate between the bytes of the 
		file and the characters used in the returned stream. If an encoding 
		is specified then the returned stream is always a unicode character stream. 
		This must be None if the mode specifies binary. 
	
	:param errors: Optional string that specifies how encoding/decoding errors 
		are handled, such as 'strict', 'ignore', 'replace'; see documentation of 
		io module for more details. 
	
	:param kwargs: Any additional args to be passed to open() or io.open(). 
	
	:return: A file stream, either using unicode characters or binary bytes. 
		This stream should be closed when no longer required.
	
	"""
	assert path
	# sanity check to avoid accidentally creating files in cwd rather than test output directory
	assert os.path.isabs(path), path
	
	if encoding:
		__log.debug('Opening file using encoding=%s: %s', encoding, path)
	
	from pysys.utils.fileutils import toLongPathSafe # import here to avoid circular dependency
	path = toLongPathSafe(path, onlyIfNeeded=True)
	
	if encoding: assert 'b' not in mode, 'cannot open file %s with binary mode %s as an encoding was specified'%(path, mode)
	return io.open(path, mode=mode, encoding=encoding, errors=errors, **kwargs)

from enum import Enum

# Rather than types.MappingProxyType, subclass dict so it's copyable
class makeReadOnlyDict(dict):
		def __readonly__(self, *args, **kwargs):
				raise RuntimeError("Cannot modify read-only dict %r"%self)
		__setitem__ = __readonly__
		__delitem__ = __readonly__
		pop = __readonly__
		popitem = __readonly__
		clear = __readonly__
		update = __readonly__
		setdefault = __readonly__
		del __readonly__
		
		def __copy__(self): return dict(self)
		def __deepcopy__(self, memo): return copy.deepcopy(dict(self))

from pysys.utils.misc import quoteString as quotestring # for pre-2.0 compatibility
