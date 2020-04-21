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



from __future__ import print_function
import os.path, logging, copy

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filediff import trimContents
from pysys.utils.pycompat import openfile
from pysys.utils.fileutils import pathexists

log = logging.getLogger('pysys.assertions')

def getmatches(file, regexpr, ignores=None, encoding=None):
	"""Look for matches on a regular expression in an input file, return a sequence of the matches.
	
	@param file: The full path to the input file
	@param regexpr: The regular expression used to search for matches
	@param ignores: A list of regexes which will cause matches to be discarded
	@param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	@return: A list of the match objects 
	@rtype: list
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	matches = []
	rexp = re.compile(regexpr)
	
	log.debug("Looking for expression \"%s\" in input file %s" %(regexpr, file))
	
	if not pathexists(file):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(file)))
	else:
		with openfile(file, 'r', encoding=encoding) as f:
			for l in f:
				match = rexp.search(l)
				if match is not None: 
					shouldignore = False
					if ignores:
						for i in ignores:
							if re.search(i, l):
								shouldignore = True
								break
					if shouldignore: continue
					
					log.debug(("Found match for line: %s" % l).rstrip())
					matches.append(match)
		return matches


def filegrep(file, expr, ignores=None, returnMatch=False, encoding=None):
	"""Search for matches to a regular expression in an input file, returning true if a match occurs.
	
	@param file: The full path to the input file
	@param expr: The regular expression (uncompiled) to search for in the input file
	@param ignores: Optional list of regular expression strings to ignore when searching file. 
	@param returnMatch: return the regex match object instead of a simple boolean
	@param encoding: Specifies the encoding to be used for opening the file, or None for default. 

	@returns: success (True / False), unless returnMatch=True in which case it returns the regex match 
		object (or None if not matched)
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not pathexists(file):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(file)))
	else:
		f = openfile(file, 'r', encoding=encoding)
		try:
			if log.isEnabledFor(logging.DEBUG):
				contents = f.readlines()
				logContents("Contents of %s;" % os.path.basename(file), contents)
			else:
				contents = f
			
			ignores = [re.compile(i) for i in (ignores or [])]
			
			regexpr = re.compile(expr)
			for line in contents:
				m = regexpr.search(line)
				if m is not None: 
					if not any([i.search(line) for i in ignores]): 
						if returnMatch: return m
						return True
			if returnMatch: return None
			return False
		finally:
			f.close()


def lastgrep(file, expr, ignore=[], include=[], encoding=None):
	"""Search for matches to a regular expression in the last line of an input file, returning true if a match occurs.
	
	@param file: The full path to the input file
	@param expr: The regular expression (uncompiled) to search for in the last line of the input file
	@returns: success (True / False)
	@param ignore: A list of regular expressions which remove entries in the input file contents before making the grep
	@param include: A list of regular expressions used to select lines from the input file contents to use in the grep 
	@param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	@rtype: integer
	@raises FileNotFoundException: Raised if the input file does not exist
	
	"""
	if not pathexists(file):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(file)))
	else:
		with openfile(file, 'r', encoding=encoding) as f:
			contents = f.readlines()
		contents = trimContents(contents, ignore, exclude=True)
		contents = trimContents(contents, include, exclude=False)
		
		logContents("Contents of %s after pre-processing;" % os.path.basename(file), contents)
		if len(contents) > 0:
			line = contents[len(contents)-1]
			regexpr = re.compile(expr)
			if regexpr.search(line) is not None: return True
		return False


def orderedgrep(file, exprList, encoding=None):
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
	@param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	@returns: None on success, or on failure the string expression that was not found. 
	@rtype: string
	@raises FileNotFoundException: Raised if the input file does not exist
		
	"""
	list = copy.deepcopy(exprList)
	list.reverse()
	
	expr = list.pop()
	regexpr = re.compile(expr)

	if not pathexists(file):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(file)))
	
	with openfile(file, 'r', encoding=encoding) as f:
		for line in f:
			if regexpr.search(line) is not None:
				if len(list) == 0:
					return None # success - found them all
				
				expr = list.pop()
				regexpr = re.compile(expr)

	return expr # the expression we were trying to match


def logContents(message, list):
	"""Log a list of strings, prepending the line number to each line in the log output.
	
	@param list: The list of strings to log
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
