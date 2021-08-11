#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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
Miscellanous utilities such as `pysys.utils.misc.compareVersions`, `pysys.utils.misc.setInstanceVariablesFromDict`, 
and `pysys.utils.misc.quoteString`.
"""

import logging
import re

__all__ = [
	'setInstanceVariablesFromDict',
	'compareVersions', 
	'quoteString',
]

def quoteString(s):
	""" Adds double quotation marks around the specified character or byte string, 
	and additional escaping only if needed to make the meaning clear, but trying to 
	avoid double-slashes unless actually needed since it makes paths harder to read. 
	
	If a byte string is provided then the 
	``repr()`` representation is used instead. 
	"""
	# this function exists primarily to provide the same quoting behaviour 
	# for str/unicode in Python 2 and str in Python 3, but avoiding 
	# the confusing "b'valuehere'" representation that "%s" would 
	# produce for python 3 bytes objects
	r = repr(s)
	if not isinstance(s, str): return r
	
	if '\\' in r.replace('\\\\',''): # if it contains escape sequences like \n to \" we'd better just use repr so it's unambiguous
		return r
	
	# repr uses single quotes, so using double quotes is a good way to make it distinguishable 
	# (the other option would be using r'...' since essentially this is like a Python raw string

	return '"%s"'%s

def compareVersions(v1, v2):
	""" Compares two alphanumeric dotted version strings to see which is more recent. 
	
	See L{pysys.process.user.ProcessUser.compareVersions} for more details. 
	"""
	
	def normversion(v):
		# convert from bytes to strings if necessary
		if isinstance(v, bytes): v = v.decode('utf-8')
		
		# normalize versions into a list of components, with integers for the numeric bits
		v = [int(x) if x.isdigit() else x for x in re.split(u'([0-9]+|[.])', v.lower().replace('-','.').replace('_','.')) if (x and x != u'.') ]
		
		return v
	
	v1 = normversion(v1)
	v2 = normversion(v2)
	
	# make them the same length
	while len(v1)<len(v2): v1.append(0)
	while len(v1)>len(v2): v2.append(0)

	for i in range(len(v1)):
		if type(v1[i]) != type(v2[i]): # can't use > on different types
			if type(v2[i])==int: # define string>int
				return +1
			else:
				return -1
		else:
			if v1[i] > v2[i]: return 1
			if v1[i] < v2[i]: return -1
	return 0

def getTypedValueOrDefault(key, value, default):
	"""
	Convert a string value to the required type matching the specified default value, or return the default if value is None. 

	
	.. versionadded:: 1.6.0
	
	:param str key: The name of the property for use in error messages.
	
	:param str value: The value that will be converted to the type of default. 
	
		If this is None, the default will be returned instead. 
		
		If this is an empty string then depending on the type of default, a boolean False, empty list[] or empty string will be returned; 
		if instead you wish empty string to result in the default being returned, pass ``value or default`` instead of ``value``. 
		
		List entries are delimited by newline and/or commas and stripped of whitespace. 
		
	:param bool/int/float/str/list[str] default: The default value to return if the property is not set or is an empty string. 
		The type of the default parameter will be used to convert the property value from a string if it is 
		provided. An exception will be raised if the value is non-empty but cannot be converted to the indicated type. 
		
	:return: A value of the same type as ``default``.
	:raises Exception: If the value cannot be converted to default.
	"""
	if value is None: return default
	if not isinstance(value, str): return value
	if default is True or default is False:
		if value.lower()=='true': return True
		if value.lower()=='false' or value=='': return False
		raise Exception('Unexpected value for boolean value %s=%s'%(key, value))
	elif isinstance(default, int):
		return int(value)
	elif isinstance(default, float):
		return float(value)
	elif isinstance(default, list):
		return [v.strip() for v in value.replace(',','\n').split('\n') if v.strip()]
	elif isinstance(default, str):
		return value # nothing to do. allow it to be empty string
	else:
		raise Exception('Unsupported type for "%s" value default: %s'%(key, type(default).__name__))


def setInstanceVariablesFromDict(obj, d, errorOnMissingVariables=False):
	"""
	Sets an instance variable for each item in the specified dictionary, with automatic conversion of 
	bool/int/float/list[str] values from strings if a default value of that type was provided as a static variable on 
	the object. 
	
	.. versionadded:: 1.6.0

	:param object obj: Any Python object. 
	:param dict[str,str] d: The properties to set
	:param bool errorOnMissingVariables: Set this to True if you want an exception to be raised if the dictionary 
		contains a key for which is there no corresponding variable on obj.
	"""
	for key, val in d.items():
		if errorOnMissingVariables and not hasattr(obj, key):
			raise KeyError('Cannot set unexpected property "%s" on %s'%(key, type(obj).__name__))
		defvalue = getattr(obj, key, None)
		if defvalue is not None and isinstance(val, str):
			# attempt type coersion to keep the type the same
			val = getTypedValueOrDefault(key, val, defvalue)
		setattr(obj, key, val)
	