#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018 M.B.Grieve

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
pycompat is a small PySys module containing a minimal set of utilities for 
writing single-source Python that runs in multiple python versions, for 
example both Python 2 and Python 3. 

"""

import sys, os, io, locale
import logging
__log = logging.getLogger('pysys.pycompat')

PY2 = sys.version_info[0] == 2

string_types = (basestring,) if PY2 else (str,)

binary_type = str if PY2 else bytes

def isstring(s): 
	""" Returns True if the specified object is a python string. 
	On Python 2 this could be a unicode character string or a byte str, 
	on python 3 this must be a character str. 
	"""
	return isinstance(s, string_types)

def quotestring(s):
	""" Adds double quotation marks around the specified character string 
	(but does not escape quotes contained within it). 
	If a byte string is provided and this is Python 3+ then the 
	'repr' representation is used instead. 
	"""
	# this function exists to provide the same quoting behaviour 
	# for str/unicode in Python 2 and str in Python 3, but avoiding 
	# the confusing "b'valuehere'" representation that "%s" would 
	# produce for python 3 bytes objects
	return '"%s"'%s if isstring(s) else repr(s)
	
def openfile(path, mode='r', encoding=None, errors=None, **kwargs):
	"""
	Opens the specified file, following the default 
	"open()" semantics for this Python version unless an encoding is 
	explicitly specified, in which case a file stream 
	yielding (unicode) character strings is always returned. 
	
	Specifically:
	
	On Python 3 this method returns a file stream yielding character strings 
	unless a binary mode was specified in which case a stream yielding 
	bytes is returned. 
	
	On Python 2 this method returns a file stream yielding unicode 
	character strings only if an encoding was explicitly specified; 
	otherwise it returns a file stream yielding "str" bytes objects. 
	
	@param path: The path to open; must be an absolute path. 
	Even on Windows this path can be long (e.g. more than the usual 256 
	character Windows limit). 
	
	@param mode: The file mode, e.g. 'r' for reading, 'wb' for binary writing. 
	
	@param encoding: The encoding to use to translate between the bytes of the 
	file and the characters used in the returned stream. If an encoding 
	is specified then the returned stream is always a unicode character stream. 
	This must be None if the mode specifies binary. 
	
	@param errors: Optional string that specifies how encoding/decoding errors 
	are handled, such as 'strict', 'ignore', 'replace'; see documentation of 
	io module for more details. The value of this attribute is ignored 
	if using the python 2 open() built-in with bytes mode that does not support it. 
	
	@param kwargs: Any additional args to be passed to open() or io.open(). 
	
	@return: A file stream, either using unicode characters or binary bytes. 
	This stream should be closed when no longer required.
	
	"""
	assert path
	# sanity check to avoid accidentally creating files in cwd rather than test output directory
	assert os.path.isabs(path), path
	
	if encoding:
		__log.debug('Opening file using encoding=%s: %s', encoding, path)
	
	from pysys.utils.fileutils import toLongPathSafe # import here to avoid circular dependency
	path = toLongPathSafe(path, onlyIfNeeded=True)
	
	if encoding or (not PY2):
		if encoding: assert 'b' not in mode, 'cannot open file %s with binary mode %s as an encoding was specified'%(path, mode)
		return io.open(path, mode=mode, encoding=encoding, errors=errors, **kwargs)
	return open(path, mode=mode, **kwargs)

if PY2:
	Enum = object
	"""In Python 2 an enumeration can be simulated by just assigning 
	constant values with a unique value (perhaps a string) as 
	statics in a simple object, e.g. ::
	
		class MyEnum(Enum):
			OPTION1 = 'MyEnum.OPTION1'
			OPTION2 = 'MyEnum.OPTION2'
			
		val = getattr(MyEnum, 'option1'.upper(), None)
		if val is None: raise Exception('Bad option: "%s"'%...)
	"""
else:
	from enum import Enum
