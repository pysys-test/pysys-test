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
Reading .properties files.
"""

import sys, os, collections
import logging
from pysys.utils.pycompat import openfile, PY2

__all__ = ['readProperties']

def readProperties(path, encoding='utf-8-sig'):
	"""
	Reads keys and values from the specified ``.properties`` file. 
	
	Support ``#`` and ``!`` comments but does not perform any special handling of backslash ``\\`` characters 
	(either for escaping or for line continuation). Leading and trailing whitespace around keys and values 
	is stripped. 
	
	:param str path: The path to the properties file. 
	:param str encoding: The encoding to use (unless running under Python 2 in which case byte strings are always returned). 
		The default is UTF-8 (with optional Byte Order Mark). 
	:return dict[str:str]: An ordered dictionary containing the keys and values from the file. 
	"""
	result = collections.OrderedDict()
	with openfile(path, mode='r', encoding=None if PY2 else encoding, errors='strict') as fp:
		for line in fp:
			line = line.lstrip()
			if len(line)==0 or line.startswith(('#','!')): continue
			line = line.split('=', 1)
			if len(line) != 2: continue
			result[line[0].strip()] = line[1].strip()

	return result
		