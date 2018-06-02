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

# Contact: moraygrieve@users.sourceforge.net

"""
	pycompat is a small PySys module containing a minimal set of utilities for 
	writing single-source Python that runs in multiple python versions, for 
	example both Python 2 and Python 3. 
"""

import sys

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