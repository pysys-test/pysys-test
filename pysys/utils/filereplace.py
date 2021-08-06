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
Replacing tokens in a text file. 
"""

import os.path

from pysys.exceptions import *
from pysys.utils.pycompat import openfile

def replace(input, output, dict={}, marker='', encoding=None):
	"""Read an input file, and write to output tailoring the file to replace set keywords with values.

	:deprecated: It is recommended to use `pysys.basetest.BaseTest.copy()` instead of this method. 

	The replace method reads in the contents of the input file line by line, checks for matches in 
	each line to the keys in the dictionary dict parameter, and replaces each match with the value
	of the dictionary for that key, writing the line to the output file. The marker parameter is a
	character which can be used to denoted keywords in the file to be replaced. For instance, with 
	dict of the form C{{'CATSEAT':'mat', 'DOGSEAT':'hat'}}, marker set to '$', and an input file::
	
	  The cat sat on the $CATSEAT$
	  The dog sat on the $DOGSEAT$
	  
	the ouptut file produced would have the contents::
	  
	  The cat sat on the mat
	  The dog sat on the hat

	:param input: The full path to the input file
	:param output: The full path to the output file with the keywords replaced
	:param dict: A dictionary of key/value pairs to use in the replacement
	:param marker: The character used to mark key words to be replaced (may be the empty string
	               if no characters are used)
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	:raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not os.path.exists(input):
		raise FileNotFoundException("unable to find file %s" % (input))
	else:
		with openfile(input, 'r', encoding=encoding) as fi, openfile(output, 'w', encoding=encoding) as fo:
			for line in fi.readlines():
				for key in list(dict.keys()):
					line = line.replace('%s%s%s'%(marker, key, marker), "%s" % (dict[key]))
				fo.write(line)

	
