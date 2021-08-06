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
Comparing (diffing) text file contents.
"""

from __future__ import print_function
import os.path, copy, difflib
import logging

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.pycompat import openfile, isstring
from pysys.utils.fileutils import pathexists

log = logging.getLogger('pysys.assertions')

def trimContents(contents, expressions, exclude=True, flags=0):
	"""Reduce a list of strings based by including/excluding lines which match any of a set of regular expressions, returning the processed list.
	
	The method reduces an input list of strings based on whether each string matches or does not match a 
	list of regular expressions.
	
	:param contents: The input list of strings to trim based on matches to regular expressions
	:param expressions: The input list of regular expressions
	:param exclude: If true any matches to the regular expressions exclude the line, if false any matches include the line
	:return: The processed list
	:rtype: list
	"""
	if len(expressions) == 0:
		return contents
	
	regexp = []
	for i in range(0, len(expressions)):
		regexp.append(re.compile(expressions[i], flags=flags))
	
	list = copy.deepcopy(contents)
	for i in range(0, len(contents)):
		anymatch = False
		for e in regexp:
			if e.search(contents[i]): 
				anymatch = True
				break
		
		if (exclude and anymatch) or (not exclude and not anymatch):
			list.remove(contents[i])

	return list



def replace(list, replacementList, flags=0):
	"""Replace all occurrences of keyword values in a list of strings with a set value, returning the processed list.
	
	The replacementList parameter should contain a list of tuples to use in the replacement, e.g. 
	[('foo', 'bar'), ('swim', 'swam')].
	
	:param list: The input list of strings to performed the replacement on
	:param replacementList: A list of tuples (key, value) where matches to key are replaced with value
	:return: The processed list
	:rtype: list
	
	"""
	for pair in replacementList:
		assert not isstring(pair), 'Each item in the replacement list must be a tuple of (string,string)'
		x, y = pair
		regexp = re.compile(pair[0], flags=flags)
		for j in range(0, len(list)):
			list[j] = re.sub(regexp, pair[1], list[j])

	return list



def logContents(message, list):
	"""Log a list of strings, prepending the line number to each line in the log output.
	
	:param list: The list of strings to log
	"""
	if not log.isEnabledFor(logging.DEBUG): return
	count = 0
	log.debug(message)
	for line in list:
		count = count + 1
		log.debug("  Line %-5d:  %s" % (count, line))



def filediff(file1, file2, ignore=[], sort=True, replacementList=[], include=[], unifiedDiffOutput=None, encoding=None, stripWhitespace=True, flags=0):
	"""Perform a file comparison between two (preprocessed) input files, returning true if the files are equivalent.
	
	The method reads in the files and loads the contents of each as a list of strings. The two files are 
	said to be equal if the two lists are equal. The method allows for preprocessing of the string lists 
	to trim down their contents prior to the comparison being performed. Preprocessing is either to remove 
	entries from the lists which match any entry in a set of regular expressions, include only lines which 
	match any entry in a set of regular expressions, replace certain keywords in the string values of each list
	with a set value (e.g. to replace time stamps etc), or to sort the lists before the comparison (e.g. where 
	determinism may not exist). Verbose logging of the method occurs at DEBUG level showing the contents of the 
	processed lists prior to the comparison being performed.  
	
	:param file1: The full path to the first file to use in the comparison
	:param file2: The full path to the second file to use in the comparison, typically a reference file
	:param ignore: A list of regular expressions which remove entries in the input file contents before making the comparison
	:param sort: Boolean to sort the input file contents before making the comparison
	:param replacementList: A list of tuples (key, value) where matches to key are replaced with value in the input file contents before making the comparison
	:param stripWhitespace: If True, every line has leading and trailing whitespace stripped before comparison, 
		which means indentation differences and whether the file ends with a blank line do not affect the outcome. 
		If False, only newline characters are stripped. 
	:param include: A list of regular expressions used to select lines from the input file contents to use in the comparison 
	:param unifiedDiffOutput: If specified, indicates the full path of a file to which unified diff output will be written, 
		if the diff fails. 
	:param encoding: Specifies the encoding to be used for opening the file, or None for default. 
	
	:return: success (True / False)
	:rtype: boolean
	:raises FileNotFoundException: Raised if either of the files do not exist

	"""
	for file in file1, file2:
		if not pathexists(file):
			raise FileNotFoundException("unable to find file \"%s\"" % file)
	else:
		stripchars = None if stripWhitespace else '\r\n' # None means all whitespace

		with openfile(file1, 'r', encoding=encoding) as f:
			list1 = [i.strip(stripchars) for i in f]

		with openfile(file2, 'r', encoding=encoding) as f:
			list2 = [i.strip(stripchars) for i in f]
		
		list1 = trimContents(list1, ignore, exclude=True, flags=flags)
		list2 = trimContents(list2, ignore, exclude=True, flags=flags)
		list1 = trimContents(list1, include, exclude=False, flags=flags)
		list2 = trimContents(list2, include, exclude=False, flags=flags)
		list1 = replace(list1, replacementList, flags=flags)
		list2 = replace(list2, replacementList, flags=flags)
		if sort:
			list1.sort()
			list2.sort()

		logContents("Contents of %s after pre-processing;" % os.path.basename(file1), list1)
		logContents("Contents of %s after pre-processing;" % os.path.basename(file2), list2)		
		if not list1 and not list2:
			# maybe this should be an exception... it's probably not what was intended
			log.warning('File comparison pre-processing has filtered out all lines from the files to be diffed, please check if this is intended: %s, %s', os.path.basename(file1), os.path.basename(file2))
			
		if list1 != list2:
			log.debug("Unified diff between pre-processed input files;")
			l1 = []
			l2 = []
			for i in list1: l1.append("%s\n"%i)
			for i in list2: l2.append("%s\n"%i)

			file1display = file1
			file2display = file2
			try:
				commonprefix = os.path.commonprefix([file1display, file2display])
			except ValueError: pass
			else:
				if commonprefix:
					# heuristic to give a longer prefix than just basename (to distinguish reference+output files with same basename)
					file1display = file1display[len(commonprefix):]
					file2display = file2display[len(commonprefix):]

			# nb: have to switch 1 and 2 around to get the right diff for a typical output,ref file pair
			diff = ''.join(difflib.unified_diff(l2, l1, 
				fromfile='%s (%d lines)'%(file2display, len(l2)),
				tofile='%s (%d lines)'%(file1display, len(l1)),
				))
			if unifiedDiffOutput:
				with openfile(unifiedDiffOutput, 'w', encoding=encoding) as f:
					f.write(diff)
			for line in diff.split('\n'): log.debug("  %s", line)

		if list1 == list2: return True
		return False



# entry point for running the script as an executable
if __name__ == "__main__":  # pragma: no cover (undocumented, little used executable entry point)
	if len(sys.argv) < 3:
			print("Usage: filediff.py <file1> <file2> [regexpr1 [regexp2]...]")
			sys.exit()
	else:	
		ignore = []
		for i in range(3,len(sys.argv)):
			ignore.append(sys.argv[i])
	 
		try:
			status = filediff(sys.argv[1], sys.argv[2], ignore)
		except FileNotFoundException as value:
			print("caught %s: %s" % (sys.exc_info()[0], value))
			print("unable to diff files... exiting")
		else:
			if status == True:
				print("No differences detected")
			else:
				print("Differences detected")
			


