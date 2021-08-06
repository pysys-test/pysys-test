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
Counting the number of lines in a text file matching a specified regular expression. 
"""

from __future__ import print_function
import sys

from pysys.exceptions import *
from pysys.utils.filegrep import getmatches

def linecount(file, regexpr=None, ignores=None, encoding=None, flags=0, **kwargs):
	"""Count the number of lines in an input file matching a regular expression, return the count.
	
	If the input regular expression is set to None, the method returns a count of the 
	number of lines in the input file. The regular expression should be passed in as 
	a string, i.e. C{"[a-z]_foo.*"} etc.
	
	:param file: The full path to the input file
	:param regexpr: The regular expression used for counting matches
	:param ignores: A list of regular expressions that will cause lines to be excluded from the count
	:return: The number of matching lines in the input file 
	:rtype: integer
	:param encoding: Specifies a non-default encoding to be used for opening the file. 
	:raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	matches = getmatches(file, regexpr, ignores=ignores, encoding=encoding, flags=flags, **kwargs)
	return len(matches)


# entry point for running the script as an executable
if __name__ == "__main__":  # pragma: no cover (undocumented, little used executable entry point)
	try:
		if len(sys.argv) == 3:
			count = linecount(sys.argv[1], sys.argv[2])
		elif len(sys.argv) == 2:
			count = linecount(sys.argv[1])
		else:
			print("Usage: lineCount.py <file> [regexpr]")
			sys.exit()

		print("Line count =	 %d" % (count))

	except FileNotFoundException as value:
		print("caught %s: %s" % (sys.exc_info()[0], value))
		print("unable to perform line count... exiting")
