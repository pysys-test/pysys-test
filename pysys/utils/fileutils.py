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

def toLongPathSafe(path, onlyIfNeeded=False):
	"""
	Converts the specified path string to a form suitable for passing to API 
	calls if it exceeds the maximum path length on this OS. 
	
	Currently, this is necessary only on Windows, where a unicode string 
	starting with \\?\ must be used to get correct behaviour for long paths. 
	On Windows this function also normalizes the capitalization of drive 
	letters so they are always upper case regardless of OS version and current 
	working directory. 
	
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
	Note that the conversion to unicode requires a lot of care on Python 2 
	where byte strings are more common, since it is not possible to combine 
	unicode and byte strings (if tjhey have non-ascii characters), for example 
	for a log statement. 
	
	"""
	if (not IS_WINDOWS) or (not path): return path
	if path[0] != path[0].upper(): path = path[0].upper()+path[1:]
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

def fromLongPathSafe(path):
	"""
	Strip off \\?\ prefixes added by L{toLongPathSafe}. 
	
	Note that this function does not convert unicode strings back to byte 
	strings, so if you want a complete reversal of toLongPathSafe you will 
	additionally have to call C{result.encode(locale.getpreferredencoding())}.
	"""
	if not path: return path
	if not path.startswith('\\\\?\\'): return path
	if path.startswith('\\\\?\\UNC\\'):
		result = '\\'+path[7:]
	else:
		result = path[4:]
	return result

def pathexists(path):
	""" Returns True if the specified path is an existing file or directory, 
	as returned by C{os.path.exists}. 
	
	This method is safe to call on paths that may be over the Windows 256 
	character limit. 
	
	@param path: If None or empty, returns True. Only Python 2, can be a 
	unicode or byte string. 
	"""
	return path and os.path.exists(toLongPathSafe(path))

def mkdir(path):
	"""
	Create a directory, with recursive creation of any parent directories.
	
	This function is a no-op (does not throw) if the directory already exists. 

	@return: Returns the path passed in. 
	"""
	origpath = path
	path = toLongPathSafe(path, onlyIfNeeded=True)
	try:
		os.makedirs(path)
	except Exception as e:
		if not os.path.isdir(path):
			# occasionally fails on windows for no reason, so add retry
			time.sleep(0.1)
			os.makedirs(path)
	return origpath

def deletedir(path, retries=1):
	"""
	Recursively delete the specified directory. 
	
	Does nothing if it does not exist. Raises an exception if the deletion fails. 
	
	@param retries: The number of retries to attempt. This can be useful to 
	work around temporary failures causes by Windows file locking. 
	"""
	path = toLongPathSafe(path)
	try:
		shutil.rmtree(path)
	except Exception: # pragma: no cover
		if not os.path.exists(path): return # nothing to do
		if retries <= 0:
			raise
		time.sleep(0.5) # work around windows file-locking issues
		deletedir(path, retries = retries-1)

