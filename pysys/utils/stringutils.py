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


from pysys.constants import *
from pysys.utils.pycompat import *

"""
Utility methods involving string manipulation. 
"""

__all__ = [
	'compareVersions',
]

def compareVersions(v1, v2):
	""" Compares two alphanumeric dotted version strings to see which is more recent. 
	
	See L{pysys.process.user.ProcessUser.compareVersions} for more details. 
	"""
	
	def normversion(v):
		# convert from bytes to strings if necessary
		if isinstance(v, binary_type): v = v.decode('utf-8')
		
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