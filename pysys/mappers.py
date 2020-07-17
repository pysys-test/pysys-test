#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
Mappers that filter or transform lines of input, for use with methods such as `pysys.basetest.BaseTest.copy`. 

.. autosummary::
	RegexReplace
	IncludeLinesBetween
	IncludeLinesMatching
	ExcludeLinesMatching

.. versionadded:: 1.6.0
"""

import logging
import re
from pysys.utils.pycompat import isstring

log = logging.getLogger('pysys.mappers')


class RegexReplace(object):
	"""
	Mapper that transforms lines by replacing all character sequences matching the specified regular expression. 
	
	For example::
	
		self.copy('myfile.txt', 'myfile-processed.txt', mappers=[RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')])
	
	:param str|compiled_regex regex: The regular expression to search for. 
	:param str replacement: The string to replace it with. This can contain backslash references to groups in the 
		regex; see ``re.sub()`` in the Python documentation for more information. 


	>>> RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')('Test string x=2020-07-15T19:22:34+00:00.')
	'Test string x=<timestamp>.'

	>>> RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')('Test string x=5/7/2020 19:22:34.1234.')
	'Test string x=<timestamp>.'

	>>> RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')('Test string x=20200715T192234Z.')
	'Test string x=<timestamp>.'

	>>> RegexReplace(RegexReplace.NUMBER_REGEX, '<number>')('Test string x=123.')
	'Test string x=<number>.'

	>>> RegexReplace(RegexReplace.NUMBER_REGEX, '<number>')('Test string x=-12.45e+10.')
	'Test string x=<number>.'
	"""
	
	DATETIME_REGEX = '(%s)'%'|'.join([
		'([0-9]{1,4}[/-][0-9]{1,2}[/-][0-9]{2,4}[ T]?)?[0-9]{1,2}:[0-9]{2}:[0-9]{2}([.][0-9]+|Z|[+-][0-9][0-9](:[0-9][0-9])?)?',
		'[0-9]{8}T[0-9]{6}(Z|[+-][0-9][0-9]:)?',
		])
	"""A regular expression that can be used to match timestamps in ISO 8601 format and other common alternatives such as:
	"2020-07-15T19:22:34+00:00", 
	"5/7/2020 19:22:34.1234", 
	"20200715T192234Z"
	
	"""

	NUMBER_REGEX = '[+-]?[0-9]+([.][0-9]+)?([eE][-+]?[0-9]+)?'
	"""Mapper that transforms lines, replacing all integer or floating point numbers with "<number>". 
	
	This is useful for removing ids that would diff-ing files more difficult, if you only care about validating 
	the non-numeric text.

	"""

	def __init__(self, regex, replacement):
		self.__str = 'RegexReplace(%s, %s)'%(regex, replacement)
		self.regex = re.compile(regex) if isstring(regex) else regex
		self.repl = replacement

	def __call__(self, line):
		return self.regex.sub(self.repl, line)

	def __repr__(self): return self.__str


class IncludeLinesBetween(object):
	"""
	Mapper that filters out all lines except those within a range of expressions. 
	
	This is useful when a log file contains lots of data you don't care about, in addition to some multi-line sequences 
	that you want to extract (with `pysys.basetest.BaseTest.copy`) ready for `pysys.basetest.BaseTest.assertDiff`.
	
	As this mapper is stateful, so not use a single instance of it in multiple tests (or multiple threads). 
	
	The following parameters can be either a callable/lambda that accepts an input line and returns a boolean, or a 
	regular expression string to search for in the specified line. 
	
	:param str|callable[str]->bool startAt: If it matches then the current line and subsequent lines are included 
		(not filtered out). If not specified, lines from the start of the file onwards are matched. 
		
	:param str|callable[str]->bool stopAfter: If it matches then lines after the current one are filtered out 
		(unless/until a line matching startAt is found). Includes the stop line. 
		
	:param str|callable[str]->bool stopBefore: If it matches then this line and lines after it are filtered out 
		(unless/until a line matching startAt is found). Excludes the stop line. 
		
	>>> def test_IncludeLinesBetween(mapper, input): return ','.join(x for x in (mapper(line) for line in input.split(',')) if x is not None)
	>>> test_IncludeLinesBetween( IncludeLinesBetween('start.*', 'stopafter.*'), 'a,start line,b,c,stopafter line,d,start line2,e')
	'start line,b,c,stopafter line,start line2,e'

	>>> test_IncludeLinesBetween( IncludeLinesBetween(startAt='start.*'), 'a,start line,b,c')
	'start line,b,c'

	>>> test_IncludeLinesBetween( IncludeLinesBetween(stopAfter='stopafter.*'), 'a,stopafter,b,c')
	'a,stopafter'

	>>> test_IncludeLinesBetween( IncludeLinesBetween(stopBefore='stopbefore.*'), 'a,b,stopbefore,c')
	'a,b'

	"""
	def __init__(self, startAt=None, stopAfter=None, stopBefore=None):
		self.__str = 'IncludeLinesBetween(%s)'%', '.join('%s=%s'%(k, repr(v)) for (k,v) in {
			'startAt':startAt,
			'stopAfter':stopAfter,
			'stopBefore':stopBefore,
		}.items() if v is not None)
	
		if startAt is not None and not callable(startAt): self.startAt = lambda line, startAt=startAt: re.search(startAt, line) is not None
		else: self.startAt = startAt
			
		if stopAfter is not None and not callable(stopAfter): self.stopAfter = lambda line: re.search(stopAfter, line) is not None
		else: self.stopAfter = stopAfter or (lambda line: False)
		
		if stopBefore is not None and not callable(stopBefore): self.stopBefore = lambda line: re.search(stopBefore, line) is not None
		else: self.stopBefore = stopBefore or (lambda line: False)
		
		self.__including = self.startAt is None

	def __repr__(self): return self.__str

	def fileStarted(self, srcPath, destPath, srcFile, destFile):
		# reset every time we start a new file
		self.__including = self.startAt is None

	def __call__(self, line):
		if self.__including:
			if self.stopAfter(line):
				self.__including = False
			if self.stopBefore(line):
				self.__including = False
				return None
			return line
		else:
			if self.startAt is not None and self.startAt(line):
				self.__including = True
				return line
		return None


class IncludeLinesMatching(object):
	"""
	Mapper that filters lines by including only lines matching the specified regular expression. 
	
	:param str|compiled_regex regex: The regular expression to match (use ``.*`` at the beginning to allow extra 
		characters at the start of the line).  Multiple expressions can be combined using 
		``(expr1|expr2)`` syntax. 

	>>> IncludeLinesMatching('Foo.*')('Foo bar')
	'Foo bar'

	>>> IncludeLinesMatching('bar.*')('Foo bar') is None
	True

	"""
	
	def __init__(self, regex):
		self.__str = 'IncludeLinesMatching(%s)'%(regex)
		self.regex = re.compile(regex) if isstring(regex) else regex

	def __call__(self, line):
		return None if self.regex.match(line) is None else line

	def __repr__(self): return self.__str


class ExcludeLinesMatching(object):
	"""
	Mapper that filters lines by excluding/ignoring lines matching the specified regular expression. 
	
	:param str|compiled_regex regex: The regular expression to match (use ``.*`` at the beginning to allow extra 
		characters at the start of the line).  Multiple expressions can be combined using 
		``(expr1|expr2)`` syntax. 

	>>> ExcludeLinesMatching('Foo.*')('Foo bar') is None
	True

	>>> ExcludeLinesMatching('bar.*')('Foo bar')
	'Foo bar'

	"""
	
	def __init__(self, regex):
		self.__str = 'ExcludeLinesMatching(%s)'%(regex)
		self.regex = re.compile(regex) if isstring(regex) else regex

	def __call__(self, line):
		return None if self.regex.match(line) is not None else line

	def __repr__(self): return self.__str

