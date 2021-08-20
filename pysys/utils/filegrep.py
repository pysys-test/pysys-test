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
Regular expression grep matching in text files. 
"""

from __future__ import print_function
import os.path, logging, copy

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filediff import trimContents
from pysys.utils.pycompat import openfile
from pysys.utils.fileutils import pathexists
from pysys.mappers import applyMappers

log = logging.getLogger('pysys.assertions')

def getmatches(file, regexpr, ignores=None, encoding=None, flags=0, mappers=[], returnFirstOnly=False):
	"""Look for matches on a regular expression in an input file, return a sequence of the matches 
	(or if returnFirstOnly=True, just the first).
	
	:param file: The full path to the input file
	:param regexpr: The regular expression used to search for matches
	:param mappers: A list of lambdas or generator functions used to pre-process the file's lines before looking for matches. 
	:param ignores: A list of regexes which will cause matches to be discarded. These are applied *after* any mappers. 
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	:param returnFirstOnly: If True, stops reading the file as soon as the first match is found and returns it. 
	:return: A list of the match objects, or the match object or None if returnFirstOnly is True
	:rtype: list
	:raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	matches = []
	rexp = re.compile(regexpr, flags=flags)
	
	log.debug("Looking for expression \"%s\" in input file %s" %(regexpr, file))

	if isinstance(ignores, str): ignores = [ignores] # it's easy to pass in a str by mistake and we definitely don't want to be ignoring lines containing any letter from that string!
	ignores = [re.compile(i, flags=flags) for i in (ignores or [])]

	if not pathexists(file):
		raise FileNotFoundException("unable to find file \"%s\"" % (file))
	else:
		with openfile(file, 'r', encoding=encoding) as f:
			for l in applyMappers(f, mappers):
				match = rexp.search(l)
				if match is not None: 
					shouldignore = False
					for i in ignores:
						if i.search(l):
							shouldignore = True
							break
					if shouldignore: continue
					
					log.debug(("Found match for line: %s" % l).rstrip())
					if returnFirstOnly is True: return match
					matches.append(match)
		if returnFirstOnly is True: return None
		return matches


def filegrep(file, expr, returnMatch=False, **kwargs): # pragma: no cover
	"""Search for matches to a regular expression in an input file, returning true if a match occurs.
	
	:param file: The full path to the input file
	:param expr: The regular expression (uncompiled) to search for in the input file
	:param ignores: Optional list of regular expression strings to ignore when searching file. 
	:param returnMatch: return the regex match object instead of a simple boolean
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	:param mappers: Mappers to pre-process the file. 

	:return: success (True / False), unless returnMatch=True in which case it returns the regex match 
		object (or None if not matched)
	:rtype: integer
	:raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	m = getmatches(file, expr, returnFirstOnly=True, **kwargs)
	if returnMatch: 
		return m
	else:
		return m is not None

def lastgrep(file, expr, ignore=[], include=[], encoding=None, returnMatch=False, flags=0):
	"""Search for matches to a regular expression in the last line of an input file, returning true if a match occurs.
	
	:param file: The full path to the input file
	:param expr: The regular expression (uncompiled) to search for in the last line of the input file
	:return: success (True / False)
	:param ignore: A list of regular expressions which remove entries in the input file contents before making the grep
	:param include: A list of regular expressions used to select lines from the input file contents to use in the grep 
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	:rtype: integer
	:raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not pathexists(file):
		raise FileNotFoundException("unable to find file \"%s\"" % (file)) # pragma: no cover
	else:
		with openfile(file, 'r', encoding=encoding) as f:
			contents = f.readlines()
		contents = trimContents(contents, ignore, exclude=True, flags=flags)
		contents = trimContents(contents, include, exclude=False, flags=flags)
		
		logContents("Contents of %s after pre-processing;" % os.path.basename(file), contents)
		if len(contents) > 0:
			line = contents[len(contents)-1]
			regexpr = re.compile(expr, flags=flags)
			result = regexpr.search(line)
			if result is not None: return result if returnMatch else True
		return None if returnMatch else False


def orderedgrep(file, exprList, encoding=None, flags=0):
	"""Seach for ordered matches to a set of regular expressions in an input file, returning None 
	on success, and a string indicating the missing expression something is missing.
		
	The ordered grep method will only pass if matches to the set of regular expression in the expression 
	list occur in the input file in the order they appear in the expression list. Matches to the regular expressions 
	do not have to be across sequential lines in the input file, only in the correct order. For example, for a file 
	with contents ::
	  
	    A is for apple 
	    B is for book
	    C is for cat
	    D is for dog
	
	an expression list of ["^A.*$", "^C.*$", "^D.*$"] will return true, whilst an expression list of 
	["^A.*$", "^C.$", "^B.$"] will return false.
	
	:param file: The full path to the input file
	:param exprList: A list of regular expressions (uncompiled) to search for in the input file
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	:return: None on success, or on failure the string expression that was not found (with an indicator of its index in the array). 
	:rtype: string
	:raises FileNotFoundException: Raised if the input file does not exist
		
	"""
	list = copy.deepcopy(exprList)
	list.reverse()
	
	expr, exprIndex = list.pop(), 1
	regexpr = re.compile(expr, flags=flags)

	if not pathexists(file):
		raise FileNotFoundException('unable to find file "%s"' % (file)) # pragma: no cover
	
	
	with openfile(file, 'r', encoding=encoding) as f:
		for line in f:
			if regexpr.search(line) is not None:
				if len(list) == 0:
					return None # success - found them all
				
				expr, exprIndex = list.pop(), exprIndex+1
				regexpr = re.compile(expr, flags=flags)

	return '#%d: %s'%(exprIndex, expr) # the expression we were trying to match


def logContents(message, list): # pragma: no cover
	"""Log a list of strings at debug, prepending the line number to each line in the log output.
	
	:param list: The list of strings to log
	"""
	if not log.isEnabledFor(logging.DEBUG): return
	count = 0
	log.debug(message)
	for line in list:
		count = count + 1
		log.debug(("  Line %-5d:  %s" % (count, line)).rstrip())

		

# entry point for running the script as an executable
if __name__ == "__main__":  # pragma: no cover (undocumented, little used executable entry point)
	if len(sys.argv) < 3:
		print("Usage: filegrep.py <file> <regexpr>")
		sys.exit()
	else:
		try:
			status = filegrep(sys.argv[1], sys.argv[2])
		except FileNotFoundException as value:
			print("caught %s: %s" % (sys.exc_info()[0], value))
			print("unable to perform grep... exiting")
		else:
			if status == True:
				print("Matches found")
			else:
				print("No matches found")
