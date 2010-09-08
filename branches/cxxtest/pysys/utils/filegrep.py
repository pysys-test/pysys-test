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

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filediff import trimContents


def getmatches(file, regexpr):
	"""Look for matches on a regular expression in an input file, return a sequence of the matches.
	
	@param file: The full path to the input file
	@param regexpr: The regular expression used to search for matches
	@return: A list of the match objects 
	@rtype: list
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	matches = []
	rexp = re.compile(regexpr)
	
	log.debug("Looking for expression \"%s\" in input file %s" %(regexpr, file))
	
	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		list = open(file, 'r').readlines()
		for i in range(0, len(list)):
			match = rexp.search(list[i])
			if match != None: 
				log.debug(string.rstrip("Found match for line: %s" % list[i]))
				matches.append(match)
		return matches


def filegrep(file, expr):
	"""Search for matches to a regular expression in an input file, returning true if a match occurs.
	
	@param file: The full path to the input file
	@param expr: The regular expression (uncompiled) to search for in the input file
	@returns: success (True / False)
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		contents = open(file, 'r').readlines()
		logContents("Contents of %s;" % os.path.basename(file), contents)
		regexpr = re.compile(expr)
		for line in contents:
			if regexpr.search(line) != None: return True
		return False


def lastgrep(file, expr, ignore=[], include=[]):
	"""Search for matches to a regular expression in the last line of an input file, returning true if a match occurs.
	
	@param file: The full path to the input file
	@param expr: The regular expression (uncompiled) to search for in the last line of the input file
	@returns: success (True / False)
	@param ignore: A list of regular expressions which remove entries in the input file contents before making the grep
	@param include: A list of regular expressions used to select lines from the input file contents to use in the grep 
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		contents = open(file, 'r').readlines()
		contents = trimContents(contents, ignore, exclude=True)
		contents = trimContents(contents, include, exclude=False)
		
		logContents("Contents of %s after pre-processing;" % os.path.basename(file), contents)
		if len(contents) > 0:
			line = contents[len(contents)-1]
			regexpr = re.compile(expr)
			if regexpr.search(line) != None: return True
		return False


def orderedgrep(file, exprList):
	"""Seach for ordered matches to a set of regular expressions in an input file, returning true if the matches occur in the correct order.
	
	The ordered grep method will only return true if matches to the set of regular expression in the expression 
	list occur in the input file in the order they appear in the expression list. Matches to the regular expressions 
	do not have to be across sequential lines in the input file, only in the correct order. For example, for a file 
	with contents ::
	  
	    A is for apple 
	    B is for book
	    C is for cat
	    D is for dog
	
	an expression list of ["^A.*$", "^C.*$", "^D.*$"] will return true, whilst an expression list of 
	["^A.*$", "^C.$", "^B.$"] will return false.
	
	@param file: The full path to the input file
	@param exprList: A list of regular expressions (uncompiled) to search for in the input file
	@returns: success (True / False)
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
		
	"""
	list = copy.deepcopy(exprList)
	list.reverse();
	expr = list.pop();

	if not os.path.exists(file):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		contents = open(file, 'r').readlines()	  
		for i in range(len(contents)):
			regexpr = re.compile(expr)
			if regexpr.search(r"%s"%contents[i]) != None:
				try:
					expr = list.pop();
				except:
					return None
		return expr


def logContents(message, list):
	"""Log a list of strings, prepending the line number to each line in the log output.
	
	@param list: The list of strings to log
	"""
	count = 0
	log.debug(message)
	for line in list:
		count = count + 1
		log.debug("  Line %-5d:  %s" % (count, line))

		

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
			if status == True:
				print "Matches found"
			else:
				print "No matches found"
			
				





