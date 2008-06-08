#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software

import os, os.path, sys, re, logging

from pysys.exceptions import *

# create the class logger
log = logging.getLogger('pysys.utils.linecount')

def linecount(file, regexpr=None):
	"""Count the number of lines in an input file matching a regular expression, return the count.
	
	If the input regular expression is set to None, the method returns a count of the 
	number of lines in the input file. The regular expression should be passed in as 
	a string, i.e. C{"[a-z]_foo.*"} etc.
	
	@param file: The full path to the input file
	@param regexpr: The regular expression used for counting matches
	@return: The number of matching lines in the input file
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	count = 0

	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		list = open(file, 'r').readlines()
	
		if regexpr == None:
			count = len(list)
		else:
			rexp = re.compile(regexpr)
			for i in range(0, len(list)):
				if rexp.search(list[i]) != None:
					count = count + 1
		return count



# entry point for running the script as an executable
if __name__ == "__main__":
	try:
		if len(sys.argv) == 3:
			count = linecount(sys.argv[1], sys.argv[2])
		elif len(sys.argv) == 2:
			count = linecount(sys.argv[1])
		else:
			print "Usage: lineCount.py <file> [regexpr]"
			sys.exit()

		print "Line count =	 %d" % (count)

	except FileNotFoundException, value:
		print "caught %s: %s" % (sys.exc_info()[0], value)
		print "unable to perform line count... exiting"
