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
# dealings in the software.

import os.path, sys, re, string, copy, difflib, logging

from pysys.constants import *;
from pysys.exceptions import *;

# create the class logger
log = logging.getLogger('pysys.utils.filediff')


def trimContents(contents, expressions, exclude=TRUE):
	"""Reduce a list of strings based by including/excluding lines which match a set of regular expressions, returning the processed list.
	
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
			if (exclude and regexp[j].search(contents[i]) != None) or (not exclude and regexp[j].search(contents[i]) == None):
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



def filediff(file1, file2, ignore=[], sort=TRUE, replacementList=[], include=[]):
	"""Perform a file comparison between two (preprocessed) input files, returning true if the files are equivalent.
	
	The method allows for preprocessing of the input files to trim down the files prior to the comparison 
	being performed. Preprocessing is either to remove lines from the files which match a set of regular 
	expressions, include only lines which match a set of regular expressions, replace certain keywords in 
	the input files with a set value (e.g. to replace time stamps etc), or to sort the files before the 
	comparison. Verbose logging of the method occurs at DEBUG level. 
	
	@param file1: The full path to the first file to use in the comparison
	@param file2: The full path to the second file to use in the comparison
	@param ignore: A list of regular expressions which remove matching lines in the input files before making the comparison
	@param sort: Boolean to sort the input file contents before making the comparison
	@param replacementList: A list of tuples (key, value) where matches to key are replaced with value in the input files before making the comparison
	@param include: A list of regular expressions used to select lines from the input files to use in the comparison. 
	@return: true|false
	@rtype: integer
	"""
	for file in file1, file2:
		if not os.path.exists(file):
			raise FileNotFoundException, "unable to find file %s" % (os.path.basename(file))
	else:
		list1 = []
		list2 = []

		f = open(file1, 'r')
		for i in f.readlines(): list1.append(string.strip(i))
		f.close()

		f = open(file2, 'r')
		for i in f.readlines(): list2.append(string.strip(i))
		f.close()
		
		list1 = trimContents(list1, ignore, exclude=TRUE)
		list2 = trimContents(list2, ignore, exclude=TRUE)
		list1 = trimContents(list1, include, exclude=FALSE)
		list2 = trimContents(list2, include, exclude=FALSE)
		list1 = replace(list1, replacementList)
		list2 = replace(list2, replacementList)
		if sort:
			list1.sort()
			list2.sort()

		logContents("Contents of %s after pre-processing;" % file1, list1)
		logContents("Contents of %s after pre-processing;" % file2, list2)		
			
		if list1 != list2:
			log.debug("Unified diff between pre-processed input files;")
			l1 = []
			l2 = []
			for i in list1: l1.append("%s\n"%i)
			for i in list2: l2.append("%s\n"%i)

			diff = ''.join(difflib.unified_diff(l1, l2))
			for line in string.split(diff, '\n'): log.debug("  %s", line)

		if list1 == list2: return TRUE
		return FALSE



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
			if status == TRUE:
				print "No differences detected"
			else:
				print "Differences detected"
			


