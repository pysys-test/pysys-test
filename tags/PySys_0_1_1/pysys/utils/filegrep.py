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

import os.path, sys, re, string, copy

from pysys.constants import *;
from pysys.exceptions import *;


def filegrep(file, expr):
	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		contents = open(file, 'r').read()
		regexpr = re.compile(expr)
		if regexpr.search(contents) != None:
			return TRUE
		else:
			return FALSE



def orderedgrep(file, exprList):
	list = copy.deepcopy(exprList)
	list.reverse();
	expr = list.pop();

	
	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		contents = open(file, 'r').readlines()	  
		for i in range(len(contents)):
			regexpr = re.compile(expr)
			if regexpr.search(contents[i]) != None:
				try:
					expr = list.pop();
				except:
					return None

		return expr



# entry point for running the script as an executable
if __name__ == "__main__":
	if len(sys.argv) < 3:
		print "Usage: filegrep.py <file> <regexpr>"
		sys.exit()
	else:
		try:
			status = filegrep(sys.argv[1], sys.argv[2])
		except FileNotFoundException, value:
			print "caught %s: %s" % (sys.exc_info()[0], value)
			print "unable to perform grep... exiting"
		else:
			if status == TRUE:
				print "Matches found"
			else:
				print "No matches found"
			
				





