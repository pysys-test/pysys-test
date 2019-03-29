# -*- coding: latin-1 -*-
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



import os, shutil, time, locale

from pysys.constants import IS_WINDOWS
from pysys.utils.pycompat import PY2

def fromLongPathSafe(path):
	"""
	Strip off \\?\ prefixes added by L{toLongPathSafe}. 
	"""
	if not path: return path
	if not path.startswith('\\\\?\\'): return path
	if path.startswith('\\\\?\\UNC\\'):
		return '\\'+path[7:]
	else:
		return path[4:]

def toLongPathSafe(path, onlyIfNeeded=False):
	"""
	Converts the specified path string to a form suitable for passing to API 
	calls if it exceeds the maximum path length on this OS. 
	
	Currently, this is necessary only on Windows, where a unicode string 
	starting with \\?\ must be used to get correct behaviour for long paths. 
	
	@param path: A path. Must not be a relative path. Can be None/empty. Can 
	contain ".." sequences. If possible, use a unicode character string. 
	On Python 2, byte strings are permitted and converted using 
	`locale.getpreferredencoding()`.
	
	@param onlyIfNeeded: Set to True to only adds the long path support if this 
	path exceeds the maximum length on this OS (e.g. 256 chars). You must keep 
	this at False if you will be adding extra characters on to the end of the 
	returned string. 
	
	@return: The passed-in path, possibly with a "\\?\" prefix added, 
	forward slashes converted to backslashes on Windows, and converted to 
	a unicode string. Trailing slashes may be removed. 
	
	"""
	if (not IS_WINDOWS) or (not path): return path
	if onlyIfNeeded and len(path)<255: return path
	if path.startswith('\\\\?\\'): return path
	inputpath = path
	# ".." is not permitted in \\?\ paths; normpath is expensive so don't do this unless we have to
	if '.' in path: 
		path = os.path.normpath(path)
	else:
		# path is most likely to contain / so more efficient to conditionalize this 
		path = path.replace('/','\\')
		if '\\\\' in path:
		# consecutive \ separators are not permitted in \\?\ paths
			path = path.replace('\\\\','\\')

	if PY2 and isinstance(path, str):
		path = path.decode(locale.getpreferredencoding())
	
	if path.startswith(u'\\\\'): 
		path = u'\\\\?\\UNC\\'+path.lstrip('\\') # \\?\UNC\server\share
	else:
		path = u'\\\\?\\'+path
	return path

def mkdir(path):
	"""
	Create a directory, with recursive creation of any parent directories.
	
	This function is a no-op (does not throw) if the directory already exists. 
	
	"""
	path = toLongPathSafe(path, onlyIfNeeded=True)
	try:
		os.makedirs(path)
	except Exception as e:
		if not os.path.isdir(path):
			# occasionally fails on windows for no reason, so add retry
			time.sleep(0.1)
			os.makedirs(path)

def deletedir(path):
	"""
	Recursively delete the specified directory. 
	
	Does nothing if it does not exist. Raises an exception if the deletion fails. 
	"""
	path = toLongPathSafe(path)
	try:
		shutil.rmtree(path)
	except Exception:
		if not os.path.exists(path): return # nothing to do
		raise

