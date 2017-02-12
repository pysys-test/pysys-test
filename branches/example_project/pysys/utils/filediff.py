#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

import os.path, sys, re, string, copy, difflib, logging

from pysys import log
from pysys.constants import *
from pysys.exceptions import *


def trimContents(contents, expressions, exclude=True):
	"""Reduce a list of strings based by including/excluding lines which match any of a set of regular expressions, returning the processed list.
	
	The method reduces an input list of strings based on whether each string matches or does not match a 
	list of regular expressions.
	
	@param contents: The input list of strings to trim based on matches to regular expressions
	@param expressions: The input list of regular expressions
	@param exclude: If true matches to the regular expressions exclude the line, if false matches include the line
	@return: The processed list
	@rtype: list
	"""
	if len(expressions) == 0:
		return contents
	
	regexp = []
	for i in range(0, len(expressions)):
		regexp.append(re.compile(expressions[i]))
	
	list = copy.deepcopy(contents)
	for i in range(0, len(contents)):
		for j in range(0, len(regexp)):
			if (exclude and regexp[j].search(contents[i]) is not None) or (not exclude and regexp[j].search(contents[i]) is None):
				list.remove(contents[i])
				break

	return list



def replace(list, replacementList):
	"""Replace all occurrences of keyword values in a list of strings with a set value, returning the processed list.
	
	The replacementList parameter should contain a list of tuples to use in the replacement, e.g. 
	[('foo', 'bar'), ('swim', 'swam')].
	
	@param list: The input list of strings to performed the replacement on
	@param replacementList: A list of tuples (key, value) where matches to key are replaced with value
	@return: The processed list
	@rtype: list
	
	"""
	for pair in replacementList:
		regexp = re.compile(pair[0])
		for j in range(0, len(list)):
			list[j] = re.sub(regexp, pair[1], list[j])

	return list



def logContents(message, list):
	"""Log a list of strings, prepending the line number to each line in the log output.
	
	@param list: The list of strings to log
	"""
	count = 0
	log.debug(message)
	for line in list:
		count = count + 1
		log.debug("  Line %-5d:  %s" % (count, line))



def filediff(file1, file2, ignore=[], sort=True, replacementList=[], include=[], unifiedDiffOutput=None):
	"""Perform a file comparison between two (preprocessed) input files, returning true if the files are equivalent.
	
	The method reads in the files and loads the contents of each as a list of strings. The two files are 
	said to be equal if the two lists are equal. The method allows for preprocessing of the string lists 
	to trim down their contents prior to the comparison being performed. Preprocessing is either to remove 
	entries from the lists which match any entry in a set of regular expressions, include only lines which 
	match any entry in a set of regular expressions, replace certain keywords in the string values of each list
	with a set value (e.g. to replace time stamps etc), or to sort the lists before the comparison (e.g. where 
	determinism may not exist). Verbose logging of the method occurs at DEBUG level showing the contents of the 
	processed lists prior to the comparison being performed.  
	
	@param file1: The full path to the first file to use in the comparison
	@param file2: The full path to the second file to use in the comparison, typically a reference file
	@param ignore: A list of regular expressions which remove entries in the input file contents before making the comparison
	@param sort: Boolean to sort the input file contents before making the comparison
	@param replacementList: A list of tuples (key, value) where matches to key are replaced with value in the input file contents before making the comparison
	@param include: A list of regular expressions used to select lines from the input file contents to use in the comparison 
	@param unifiedDiffOutput: If specified, indicates the full path of a file to which unified diff output will be written, 
		if the diff fails. 
	@return: success (True / False)
	@rtype: boolean
	@raises FileNotFoundException: Raised if either of the files do not exist

	"""
	for file in file1, file2:
		if not os.path.exists(file):
			raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		list1 = []
		list2 = []

		with open(file1, 'r') as f:
			for i in f: list1.append(i.strip())

		with open(file2, 'r') as f:
			for i in f: list2.append(i.strip())
		
		list1 = trimContents(list1, ignore, exclude=True)
		list2 = trimContents(list2, ignore, exclude=True)
		list1 = trimContents(list1, include, exclude=False)
		list2 = trimContents(list2, include, exclude=False)
		list1 = replace(list1, replacementList)
		list2 = replace(list2, replacementList)
		if sort:
			list1.sort()
			list2.sort()

		logContents("Contents of %s after pre-processing;" % os.path.basename(file1), list1)
		logContents("Contents of %s after pre-processing;" % os.path.basename(file2), list2)		
			
		if list1 != list2:
			log.debug("Unified diff between pre-processed input files;")
			l1 = []
			l2 = []
			for i in list1: l1.append("%s\n"%i)
			for i in list2: l2.append("%s\n"%i)

			# nb: have to switch 1 and 2 around to get the right diff for a typical output,ref file pair
			diff = ''.join(difflib.unified_diff(l2, l1, 
				fromfile='%s (%d lines)'%(os.path.basename(file2), len(l2)),
				tofile='%s (%d lines)'%(os.path.basename(file1), len(l1)),
				))
			if unifiedDiffOutput:
				with open(unifiedDiffOutput, 'w') as f:
					f.write(diff)
			for line in diff.split('\n'): log.debug("  %s", line)

		if list1 == list2: return True
		return False



# entry point for running the script as an executable
if __name__ == "__main__":
	if len(sys.argv) < 3:
			print "Usage: filediff.py <file1> <file2> [regexpr1 [regexp2]...]"
			sys.exit()
	else:	
		ignore = []
		for i in range(3,len(sys.argv)):
			ignore.append(sys.argv[i])
	 
		try:
			status = filediff(sys.argv[1], sys.argv[2], ignore)
		except FileNotFoundException, value:
			print "caught %s: %s" % (sys.exc_info()[0], value)
			print "unable to diff files... exiting"
		else:
			if status == True:
				print "No differences detected"
			else:
				print "Differences detected"
			


