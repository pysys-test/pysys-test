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
Mapper filter or transform lines of input, for use with methods such as `pysys.basetest.BaseTest.copy` 
and `pysys.basetest.BaseTest.assertGrep`. 

This package contains several pre-defined mappers:

.. autosummary::
	RegexReplace
	IncludeLinesBetween
	IncludeLinesMatching
	ExcludeLinesMatching
	JoinLines
	JoinLines.PythonTraceback
	JoinLines.JavaStackTrace
	JoinLines.AntBuildFailure
	SortLines
	applyMappers

In addition to the above, you can create custom mappers, which are usually callables (functions, lambdas, or classes 
with a ``__call__()`` method) that return the transformed copy of each incoming line. 

For advanced cases you can provide a generator function that accepts a line iterator as input and yields the mapped 
lines; this allows for stateful transformation and avoids the limitation of having a 1:1 (or 1:0) relationship between 
input and output lines. 

All lines passed to/from mappers end with a ``\\n`` character (on all platforms), except for the last line of the 
file which will only have the ``\\n`` if the file ends with a blank line. 
Mappers must always preserve the final ``\\n`` of each line (if present). 

.. versionadded:: 1.6.0
"""

import logging
import re
import inspect
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

	>>> RegexReplace(RegexReplace.DATETIME_REGEX, '<timestamp>')('Test string x=20200715T192234Z.\\n')
	'Test string x=<timestamp>.\\n'

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
	"""A regular expression that can be used to match integer or floating point numbers. This could be used in a 
	mapper to replace all numbers with with "<number>" to remove ids that would make diff-ing files more difficult, if 
	you only care about validating the non-numeric text.

	"""

	def __init__(self, regex, replacement):
		self.__str = 'RegexReplace(%s, %s)'%(regex, replacement)
		self.regex = re.compile(regex) if isstring(regex) else regex
		self.repl = replacement

	def __call__(self, line):
		return self.regex.sub(self.repl, line)

	def __repr__(self): return self.__str
	
def _createRegexMatchFunction(regex):
	# Internal helper, not public API, do not use
	
	regex = re.compile(regex)
	def matchFunction(line, *optional): return re.search(regex, line) is not None
	return matchFunction


class IncludeLinesBetween(object):
	"""
	Mapper that filters out all lines except those within a range of expressions. 
	
	This is useful when a log file contains lots of data you don't care about, in addition to some multi-line sequences 
	that you want to extract (with `pysys.basetest.BaseTest.copy`) ready for `pysys.basetest.BaseTest.assertDiff`.
	
	As this mapper is stateful, do not use a single instance of it in multiple tests (or multiple threads). 
	
	The following parameters can be either a callable/lambda that accepts an input line and returns a boolean, or a 
	regular expression string to search for in the specified line. 
	
	:param str|callable[str]->bool startAt: If it matches then the current line and subsequent lines are included 
		(not filtered out). If not specified, lines from the start of the file onwards are matched. 

	:param str|callable[str]->bool startAfter: If it matches then the subsequent lines are included 
		(not filtered out). If not specified, lines from the start of the file onwards are matched. 
		
	:param str|callable[str]->bool stopAfter: If it matches then lines after the current one are filtered out 
		(unless/until a line matching startAt is found). Includes the stop line. 
		
	:param str|callable[str]->bool stopBefore: If it matches then this line and lines after it are filtered out 
		(unless/until a line matching startAt is found). Excludes the stop line. 
		
	>>> def _mapperUnitTest(mapper, input): return '|'.join(x for x in (applyMappers([line+'\\n' for line in input.replace('<tab>', chr(9)).split('|')], [mapper])))
	>>> _mapperUnitTest( IncludeLinesBetween('start.*', 'stopafter.*'), 'a|start line|b|c|stopafter line|d|start line2|e').replace('\\n','')
	'start line|b|c|stopafter line|start line2|e'

	>>> _mapperUnitTest( IncludeLinesBetween(startAt='start.*'), 'a|start line|b|c').replace('\\n','')
	'start line|b|c'

	>>> _mapperUnitTest( IncludeLinesBetween(startAfter='start.*'), 'a|start line|b|c').replace('\\n','')
	'b|c'

	>>> _mapperUnitTest( IncludeLinesBetween(startAt=lambda l: l.startswith('start')), 'a|start line|b|c').replace('\\n','')
	'start line|b|c'

	>>> _mapperUnitTest( IncludeLinesBetween(stopAfter='stopafter.*'), 'a|stopafter|b|c').replace('\\n','')
	'a|stopafter'

	>>> _mapperUnitTest( IncludeLinesBetween(stopBefore='stopbefore.*'), 'a|b|stopbefore|c')
	'a\\n|b\\n'

	.. versionchanged:: 2.0 Added startAfter

	"""
	def __init__(self, startAt=None, stopAfter=None, startAfter=None, stopBefore=None):
		self.__str = 'IncludeLinesBetween(%s)'%', '.join('%s=%s'%(k, repr(v)) for (k,v) in {
			'startAt':startAt,
			'startAfter':startAfter,
			'stopAfter':stopAfter,
			'stopBefore':stopBefore,
		}.items() if v is not None)
	
		if startAt is not None and not callable(startAt): self.startAt = _createRegexMatchFunction(startAt)
		else: self.startAt = startAt

		if startAfter is not None and not callable(startAfter): self.startAfter = _createRegexMatchFunction(startAfter)
		else: self.startAfter = startAfter
			
		if stopAfter is not None and not callable(stopAfter): self.stopAfter = _createRegexMatchFunction(stopAfter)
		else: self.stopAfter = stopAfter or (lambda line: False)
		
		if stopBefore is not None and not callable(stopBefore): self.stopBefore = _createRegexMatchFunction(stopBefore)
		else: self.stopBefore = stopBefore or (lambda line: False)
		
		self.__including = self.startAt is None and self.startAfter is None

	def __repr__(self): return self.__str

	def fileStarted(self, srcPath, destPath, srcFile, destFile):
		# reset every time we start a new file
		self.__including = self.startAt is None and self.startAfter is None

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
			if self.startAfter is not None and self.startAfter(line):
				self.__including = True
				return None
		return None


class JoinLines(object):
	"""
	Mapper that joins/concatenates consecutive related lines together into a single line. Useful for combining error or 
	stack trace lines together for easier grepping and for more meaingful test failure reasons.
	
	There are static factory methods on this class to create pre-configured instances for common languages e.g. 
	`JoinLines.JavaStackTrace`, `JoinLines.PythonTraceback`, or you can create your own. See 
	`pysys.basetest.BaseTest.assertGrep` for an example. 
	
	As this mapper is stateful, do not use a single instance of it in multiple tests (or multiple threads). 
	
	The following parameters can be either a callable/lambda that accepts an input line and returns a boolean, or a 
	regular expression string to search for in the specified line. Note that a lambda with a simple string operation such 
	as ``startswith(...)`` is usually a lot more efficient than a regular expression. 
	
	Typically you would use startAt and just one of continueWhile/stopAfter/stopBefore.
	
	:param str|callable[str]->bool startAt: If it matches then the current line then subsequent lines are joined into one. 
		Can be a regular expression or a function with argument ``line``. 
		
	:param str|callable[str,list[str]]->bool continueWhile: After joining has started, then all consecutive lines 
		matching this will be included in the current join, and it will be stopped as soon as a non-matching line is found. 
		Can be a regular expression or a function with arguments ``(line, buffer)`` where ``buffer`` is the list of 
		previous lines accumulated from the current startAt match. 
				
	:param str|callable[str,list[str]]->bool stopAfter: After joining has started, if this matches then this is the last line to be 
		included in the current join. Includes the stop line.
		Can be a regular expression or a function with arguments ``(line, buffer)`` where ``buffer`` is the list of 
		previous lines accumulated from the current startAt match. 

	:param str|callable[str,list[str]]->bool stopBefore: After joining has started, if this matches, then the preceding line is 
		the last line to be included in the current join. Excludes the stop line. 
		Can be a regular expression or a function with arguments ``(line, buffer)`` where ``buffer`` is the list of 
		previous lines accumulated from the current startAt match. 

	:param callable[list[str]]->str combiner: A function that combines the joined lines from a given sequence 
		into a single line. The implementation is `defaultCombiner`. 
		
	>>> def _mapperUnitTest(mapper, input): return ''.join(x for x in (applyMappers([line+'\\n' for line in input.replace('<tab>', chr(9)).split('|')], [mapper]))).replace('\\n','|')
	>>> _mapperUnitTest( JoinLines(startAt='startat.*', stopAfter='stopafter.*'), 'a| startat START|  stack1|  stack2 | stopafter STOP | d|startat2| e | f ')
	'a|startat START / stack1 / stack2 / stopafter STOP| d|startat2 / e / f|'

	>>> _mapperUnitTest( JoinLines(startAt='startat.*', continueWhile='stack.*'), 'startat START|  stack1|  stack2 | stopbefore NEXT LINE|d|startat2|stopbefore2')
	'startat START / stack1 / stack2| stopbefore NEXT LINE|d|startat2|stopbefore2|'

	>>> _mapperUnitTest( JoinLines(startAt='startat.*', stopAfter='stopafter.*'), 'a| startat START|  stack1|  |  stack2 | stopafter STOP |d|startat2| stopafter e | f ')
	'a|startat START / stack1 / stack2 / stopafter STOP|d|startat2 / stopafter e| f |'

	>>> _mapperUnitTest( JoinLines(startAt='startat.*', stopBefore='stopbefore.*'), 'startat START|  stack1|  stack2 | stopbefore NEXT LINE|d|startat2|stopbefore2')
	'startat START / stack1 / stack2| stopbefore NEXT LINE|d|startat2|stopbefore2|'

	.. versionadded:: 2.0
	"""
	def __init__(self, startAt=None, continueWhile=None, stopAfter=None, stopBefore=None, combiner=None):
		assert startAt is not None
		
		if combiner is None: combiner = self.defaultCombiner
		
		self.__str = 'JoinLines(%s)'%', '.join('%s=%s'%(k, repr(v)) for (k,v) in {
			'startAt':startAt,
			'continueWhile':continueWhile,
			'stopAfter':stopAfter,
			'stopBefore':stopBefore,
			'combiner':combiner,
		}.items() if v is not None)

		if not callable(startAt): startAt = _createRegexMatchFunction(startAt)
		
		if stopAfter is not None and not callable(stopAfter): stopAfter = _createRegexMatchFunction(stopAfter)
		else: stopAfter = stopAfter or (lambda line, buffer: False)
		
		if stopBefore is not None and not callable(stopBefore): stopBefore = _createRegexMatchFunction(stopBefore)
		else: stopBefore = stopBefore or (lambda line, buffer: False)

		if continueWhile is not None and not callable(continueWhile): continueWhile = _createRegexMatchFunction(continueWhile)
		# allow continueWhile to be None
		
		def lineEndingSafeCombiner(lines):
			if len(lines) == 1: return lines[0] # don't apply combiner if we aren't joining multiple lines
			
			l = combiner(lines)
			if not l.endswith('\n'): l += '\n' # don't rely on user remembering to not strip newlines in their combiner
			return l
		
		def generatorFunction(it):
			buffer = [] # buffered lines
			for l in it:
				if len(buffer) > 0:
					if stopAfter(l, buffer):
						yield lineEndingSafeCombiner(buffer+[l])
						buffer = []
						continue
					elif stopBefore(l, buffer) or (continueWhile is not None and not continueWhile(l, buffer)):
						yield lineEndingSafeCombiner(buffer)
						buffer = []
						# don't "continue", i.e. drop down to the logic below
					else:
						buffer.append(l)
						continue
						
				if startAt(l):
					buffer.append(l)
				else:
					yield l
			# end for loop
				
			if buffer: 
					yield lineEndingSafeCombiner(buffer)
		self.__generatorFunction = generatorFunction
	
	def __repr__(self): return __str
	def __call__(self, iterator): 
		for x in self.__generatorFunction(iterator): yield x

	@staticmethod
	def defaultCombiner(lines):
		"""
		The default "combiner" function used by `JoinLines`, which joins the lines with the delimiter ``" / "`` after 
		stripping leading/trailing whitespace and blank lines.
		
		If you want different behaviour, create your own function with this signature and pass it in as the ``combiner=`` 
		argument. 
		
		:param list[str] lines: The lines to be joined. 
		:returns: A single string representing all of these lines. 
		"""
		return ' / '.join(l.strip() for l in lines if l.strip())

	@staticmethod
	def PythonTraceback():
			"""
			Mapper that joins the lines of a typical Python traceback (starting ``Traceback (most recent call last):``) 
			into a single line, for easier grepping and self-contained test outcome failure reasons.
			
			The combiner is configured to put the actual exception class and message (which is the most important information) 
			at the start of the joined line rather than at the end (after the traceback). 

			>>> def _mapperUnitTest(mapper, input): return '|'.join(x for x in (applyMappers([line for line in input.replace('|','\\n|').replace('<tab>',chr(9)).split('|')], [mapper]))).replace('\\n','')
			>>> _mapperUnitTest( JoinLines.PythonTraceback(), 'a|Traceback (most recent call last):|  File "~/foo.py", line 1195, in __call__|    def __call__(self): myfunction()|  File "~/bar.py", line 11, in myfunction |    raise KeyError ("foo bar")|KeyError: "foo bar"|Normal operation is resumed')
			'a|KeyError: "foo bar" / Traceback (most recent call last): / File "~/foo.py", line 1195, in __call__ / def __call__(self): myfunction() / File "~/bar.py", line 11, in myfunction / raise KeyError ("foo bar")|Normal operation is resumed'

			>>> _mapperUnitTest( JoinLines.PythonTraceback(), 'a|Traceback (most recent call last):|  File "~/foo.py", line 1195, in __call__|    def __call__(self): myfunction()|  File "~/bar.py", line 11, in myfunction |    raise KeyError ("foo bar")|AssertionError|Normal operation is resumed')
			'a|AssertionError / Traceback (most recent call last): / File "~/foo.py", line 1195, in __call__ / def __call__(self): myfunction() / File "~/bar.py", line 11, in myfunction / raise KeyError ("foo bar")|Normal operation is resumed'

			>>> _mapperUnitTest( JoinLines.PythonTraceback(), 'a|Traceback (most recent call last):|  File "~/foo.py", line 1195, in __call__|    def __call__(self): myfunction()|  File "~/bar.py", line 11, in myfunction |    raise KeyError ("foo bar")||KeyError: "foo bar"|Normal operation is resumed')
			'a|KeyError: "foo bar" / Traceback (most recent call last): / File "~/foo.py", line 1195, in __call__ / def __call__(self): myfunction() / File "~/bar.py", line 11, in myfunction / raise KeyError ("foo bar")|Normal operation is resumed'

			>>> _mapperUnitTest( JoinLines.PythonTraceback(), 'a|Traceback (most recent call last):|  File "~/foo.py", line 1195, in __call__|    def __call__(self): myfunction()|  File "~/bar.py", line 11, in myfunction |<tab>raise KeyError ("foo bar")||KeyError: "foo bar"|OtherError: baz|Normal operation is resumed')
			'a|KeyError: "foo bar" / Traceback (most recent call last): / File "~/foo.py", line 1195, in __call__ / def __call__(self): myfunction() / File "~/bar.py", line 11, in myfunction / raise KeyError ("foo bar")|OtherError: baz|Normal operation is resumed'

			>>> _mapperUnitTest( JoinLines.PythonTraceback(), 'a|Traceback (most recent call last):|  File "~/foo.py", line 1195, in __call__|    def __call__(self): myfunction()|  File "~/bar.py", line 11, in myfunction |    raise KeyError ("foo bar")|Normal operation is resumed')
			'a|Traceback (most recent call last): / File "~/foo.py", line 1195, in __call__ / def __call__(self): myfunction() / File "~/bar.py", line 11, in myfunction / raise KeyError ("foo bar")|Normal operation is resumed'


			"""
			def maybeReorder(lines):
				if not lines[-1].startswith(('  ', '\t', '\n')): return [lines[-1]]+lines[0:-1] # move the exception name to the beginning, if we can
				return lines
			
			return JoinLines(
				startAt=lambda l: l.startswith('Traceback (most recent call last):'),
				
				# Stop when the indenting stops, but also match the first non-indented line that starts with a Python exception class (and a preceding blank)
				continueWhile=lambda l, buffer: l.startswith(('  ', '\t', '\n')) or (len(buffer)>0 and (buffer[-1].startswith(('  ', '\t', '\n')) and re.match('^[a-zA-Z0-9._]+(: |Exception|Error)', l))),
				# Put the actual exception first (since end of message may get truncated)
				combiner=lambda lines: JoinLines.defaultCombiner(maybeReorder(lines))
				)

	@staticmethod
	def JavaStackTrace(combiner=None, errorLogLineRegex='(ERROR|FATAL) '):
			"""
			Mapper that joins the lines of a typical Java(R) stack trace (from stderr or a log file) into a single line, 
			for easier grepping and self-contained test outcome failure reasons.
			
			:param callable[list[str]]->str combiner: See `JoinLines`. 
			:param str errorLogLineRegex: A regular expression used to match log lines which could (optionally) be followed 
				by a stack trace. 

			>>> def _mapperUnitTest(mapper, input): return '|'.join(x for x in (applyMappers([line for line in input.replace('<tab>', chr(9)).split('|')], [mapper]))).replace('\\n','')
			>>> _mapperUnitTest( JoinLines.JavaStackTrace(), 'java.lang.AssertionError: Invalid state|<tab>at org.junit.Assert.fail(Assert.java:100)|Caused by: java.lang.RuntimeError: Oh dear |<tab>at org.myorg.TestMyClass2|Normal operation has resumed ')
			'java.lang.AssertionError: Invalid state / at org.junit.Assert.fail(Assert.java:100) / Caused by: java.lang.RuntimeError: Oh dear / at org.myorg.TestMyClass2|Normal operation has resumed '
			
			>>> _mapperUnitTest( JoinLines.JavaStackTrace(), '2021-05-25 ERROR [Thread1] The operation failed|java.lang.AssertionError: Invalid state|<tab>at org.junit.Assert.fail(Assert.java:100)|Caused by: java.lang.RuntimeError: Oh dear |<tab>at org.myorg.TestMyClass2|2021-05-25 ERROR [Thread1] Another error|2021-05-25 INFO [Thread1] normal operation')
			'2021-05-25 ERROR [Thread1] The operation failed / java.lang.AssertionError: Invalid state / at org.junit.Assert.fail(Assert.java:100) / Caused by: java.lang.RuntimeError: Oh dear / at org.myorg.TestMyClass2|2021-05-25 ERROR [Thread1] Another error|2021-05-25 INFO [Thread1] normal operation'

			>>> _mapperUnitTest( JoinLines.JavaStackTrace(), 'Exception in thread "main" java.lang.RuntimeException: Main exception|<tab>at scratch.ExceptionTest.main(ExceptionTest.java:16)')
			'Exception in thread "main" java.lang.RuntimeException: Main exception / at scratch.ExceptionTest.main(ExceptionTest.java:16)'

			"""
			return JoinLines(
				# Both stderr lines that begin with an exception class, and log lines containing ERROR or FATAL
				startAt='('+errorLogLineRegex+'|^[a-zA-Z.]+(Error|Exception): |Exception in thread )',
				# Stop when the indenting stops
				continueWhile=r'(^[a-zA-Z.]+(Error|Exception): |\t*Caused by: |\t*Suppressed: |\t+at |\t+[.][.][.] )',
				combiner=combiner,
				)


	@staticmethod
	def AntBuildFailure():
			"""
			Mapper that joins the lines of an ant's stderr BUILD FAILED output to actually include the failure message(s), 
			for easier grepping and self-contained test outcome failure reasons.

			As this mapper is stateful, do not use a single instance of it in multiple tests (or multiple threads). 

			>>> def _mapperUnitTest(mapper, input): return '|'.join(x for x in (applyMappers([line for line in input.split('|')], [mapper]))).replace('\\n','')
			>>> _mapperUnitTest( JoinLines.AntBuildFailure(), 'BUILD FAILED|~/build.xml:13: Unknown attribute [dodgyattribute]||Total time: 0 seconds')
			'BUILD FAILED / ~/build.xml:13: Unknown attribute [dodgyattribute]||Total time: 0 seconds'

			"""
			return JoinLines(
				startAt=lambda l: l.startswith('BUILD FAILED'),
				# Continue until we get a blank line
				continueWhile=lambda l, _: len(l.strip())>0, 
				)
	
def SortLines(key=None):
		"""
		Mapper that sorts all lines. 
		
		Note that unlike most mappers this will read the entire input into memory to perform the sort, so only use this 
		when you know the file size isn't enormous.

		As this mapper is stateful, do not use a single instance of it in multiple tests (or multiple threads). 

		.. versionadded:: 2.0

		:param callable[str]->str key: A callable that returns the sort key to use for each line, in case you want 
			something other than the default lexicographic sorting. 
		
		>>> def _mapperUnitTest(mapper, input): return '|'.join(x for x in (applyMappers([line+'' for line in input.split('|')], [mapper])))
		>>> _mapperUnitTest( SortLines(), 'a|z|A|B|aa|c').replace('\\n', '')
		'A|B|a|aa|c|z'
		
		>>> _mapperUnitTest( SortLines( key=lambda s: int(s) ), '100|1|10|22|2').replace('\\n', '')
		'1|2|10|22|100'

		>>> _mapperUnitTest( SortLines(), 'a\\n|c\\n|b')
		'a\\n|b\\n|c\\n'

		"""

		def mapperGenerator(it):
			for l in sorted(it, key=key):
				if not l.endswith('\n'): l += '\n' # need uniform newlines in output since it's possible there aren't uniform newlines in input (if file doesn't end in a newline)
				yield l
		return mapperGenerator

class IncludeLinesMatching(object):
	"""
	Mapper that filters lines by including only lines matching the specified regular expression. 
	
	:param str|compiled_regex regex: The regular expression to match (this is a match not a search, so 
		use ``.*`` at the beginning if you want to allow extra characters at the start of the line).  
		Multiple expressions can be combined using ``(expr1|expr2)`` syntax. 

	>>> IncludeLinesMatching('Foo.*')('Foo bar\\n')
	'Foo bar\\n'

	>>> IncludeLinesMatching('bar.*')('Foo bar\\n') is None
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

def applyMappers(iterator, mappers):
	"""
	A generator function that applies zero or more mappers to each line from an iterator and yields each fully mapped line. 

	If a mapper function returns None for a line that line is dropped. 

	:param Iterable[str] iterator: An iterable such as a file object that yields lines to be mapped. 
		Trailing newline characters are preserved, but not passed to the mappers. 

	:type mappers: List[callable[str]->str or callable[iterator]->Generator[str,None,None] ] 
	:param mappers: 
		A list of filter functions that will be used to pre-process each 
		line from the file (returning None if the line is to be filtered out). 
		For advanced cases where stateful mappings are needed, instead of a function to filter individual lines, you can 
		provide a generator function which accepts an iterable of all input lines from each file and yields output lines 
		(including potentially some additional lines). 
		
		Mappers must always preserve the final ``\\n`` of each line (if present). 

		Do not share mapper instances across multiple tests or threads as this can cause race conditions. 
		
		As a convenience to make conditionalization easier, any ``None`` items in the mappers list are 
		simply ignored. 
	
	:rtype: Iterable[str]
	
	.. versionadded:: 2.0
	"""
	if len(mappers)==0: # optimize for common case of zero mappers
		yield from iterator

	# strip out any noop (None) mappers
	if None in mappers: mappers = [m for m in mappers if m]
	
	# isgeneratorfunction handles both function generators, and functor classes with a __call__ method that's a generator
	def isgeneratorfunction(m):	return inspect.isgeneratorfunction(m) or inspect.isgeneratorfunction(m.__call__)
	
	# if there are any generator functions we need to be recursive
	if any(isgeneratorfunction(m) for m in mappers):
		m = mappers[0]
		if not isgeneratorfunction(m): # then make it be one, so it's all uniform
			originalMapperFunction = m
			def generatorFunctionForSimpleMapper(it):
				for originalline in it:
					l = originalMapperFunction(originalline)
					if l is not None: 
						# Mappers must be written to preserve line endings, otherwise the lines passed to the next mapper may not be correctly interpreted
						assert l.endswith('\n') or not originalline.endswith('\n'), 'Mappers must not remove newline characters: %s'%originalMapperFunction
						
						yield l
			m = generatorFunctionForSimpleMapper
		
		yield from applyMappers(m(iterator), mappers[1:])

	else: # simple, fast implementation for the non-generators case
		for originalline in iterator:
			l = originalline
			for mapper in mappers:
				l = mapper(l)
				if l is None: break
			if l is not None: 
				# Mappers must be written to preserve line endings, otherwise the lines passed to the next mapper may not be correctly interpreted
				assert l.endswith('\n') or not originalline.endswith('\n'), 'Mappers must not add/remove newline characters but one of these mappers has: %s'%mappers
				
				yield l

	