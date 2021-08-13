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
Log formatting classes that can be used or customized from the project configuration, including support for colored 
output on the console. 
"""

import copy, logging

from pysys.constants import *
from pysys.utils.pycompat import *
import pysys, threading

def stripANSIEscapeCodes(text):
	"""Remove any ANSI escape sequences (for example to set console color) present in the specified string. 
	
	..versionadded:: 1.6.0
	"""
	if not text: return text
	
	if PY2 and isinstance(text, binary_type):
		return re.sub(b'\\033\\[[0-9;]+m', b'', text)
	else:
		return re.sub(u'\\033\\[[0-9;]+m', u'', text)

class BaseLogFormatter(logging.Formatter):
	"""Base class for formatting log messages.
	
	This implementation delegates everything to logging.Formatter using the messagefmt and datefmt
	properties. Subclasses may be implemented to provide required customizations, and can be registered
	by specifying classname in the formatter node of the project configuration file.
	
	The class is constructed with a dictionary of properties, which are configured by providing
	<property name="..." value="..."/> elements or attributes on the formatter node of the project
	configuration file. Entries in the properties should be specific to the class, and removed
	when passing the properties to the super class, which will throw an exception if any unexpected
	options are present
	
	:param propertiesDict: dictionary of formatter-specific options
	"""

	# the key to add to the extra={} dict of a logger call to specify the category
	CATEGORY = 'log_category'

	# the key to add to the extra={} dict of a logger call to specify the arg index for the category
	ARG_INDEX = 'log_arg_index'

	@classmethod
	def tag(cls, category, arg_index=None):
		"""Return  dictionary to tag a string to format with color encodings.

		:param category: The category, as defined in L{ColorLogFormatter.COLOR_CATEGORIES}
		:param arg_index: The index of argument in the string expansion to color. This can be either a single
			integer value representing the index, or a list of integers representing a set of indexes to be colored. 
			Note that format arguments for coloring must be of string type. 
		:return: A dictionary that can then be used in calls to the logger
		"""
		if type(arg_index) is int: return {cls.CATEGORY:category, cls.ARG_INDEX:[arg_index]}
		if type(arg_index) is list and all(isinstance(i, int) for i in arg_index): return {cls.CATEGORY:category, cls.ARG_INDEX:arg_index}
		return {cls.CATEGORY:category}


	def __init__(self, propertiesDict):
		self.name = propertiesDict.pop('name', None) # probably not used
		
		__formatterName = propertiesDict.pop('__formatterName', None)

		super(BaseLogFormatter, self).__init__(
			propertiesDict.pop('messagefmt', DEFAULT_FORMAT),
			propertiesDict.pop('datefmt', '%H:%M:%S' if __formatterName=='stdout' else None) )
		assert not isinstance(self._fmt, binary_type), 'message format must be a unicode not a byte string otherwise % arg formatting will not work consistently'
		if propertiesDict: raise Exception('Unknown formatter option(s) specified: %s'%', '.join(list(propertiesDict.keys())))


class ColorLogFormatter(BaseLogFormatter):
	"""Formatter supporting colored output to a console.
	
	This implementation supports color coding of messages based on the category of the message,
	and the index of the string in the format encoding. This implementation is the default for
	console output, with the color coding enabled either by the color option on the formatter
	set to true. 
	
	The ``PYSYS_COLOR`` environment variable can be set to true or false, overriding any 
	setting specified in the project configuration.
	
	The colors used for each category defined by this class can be overridden 
	by specifying "color:XXX" options, e.g.::

		<formatter><property name="color:dumped core" value="YELLOW"/></formatter>

	:ivar dict(str,str) COLOR_CATEGORIES: the color map for the defined logging categories
	:ivar dict(str,str) COLOR_ESCAPE_CODES: the escape codes for each of the support colors

	"""
	# use a lookup map from message "categories" to colors,
	COLOR_CATEGORIES = {
		LOG_WARN:'MAGENTA',
		LOG_ERROR:'RED',
		LOG_TRACEBACK:'RED',
		LOG_DEBUG:'BLUE',
		LOG_FILE_CONTENTS:'BLUE',
		LOG_TEST_DETAILS:'CYAN',
		LOG_TEST_OUTCOMES: 'CYAN',
		LOG_TEST_PROGRESS: 'CYAN',
		LOG_TEST_PERFORMANCE: 'CYAN',
		LOG_TIMEOUTS: 'MAGENTA',
		LOG_FAILURES: 'RED',
		LOG_PASSES: 'GREEN',
		LOG_SKIPS: 'YELLOW',
		LOG_DIFF_ADDED: 'CYAN', LOG_DIFF_REMOVED: 'MAGENTA', # can't use red/green here without confusion with fail/pass
		LOG_END:'END',
	}
	
	# by default we use standard ANSI escape sequences, supported by most unix terminals
	COLOR_ESCAPE_CODES = {
		'BLUE':    '',
		'GREEN':   '',
		'YELLOW':  '',
		'RED':     '',
		'MAGENTA': '',
		'CYAN':    '',
		'WHITE':   '',
		'BLACK':   '',
		'END':     '',
	}

	@staticmethod
	def configureANSIEscapeCodes(bright=None):
		"""Sets the ANSI escape codes to be used, either using the extended 
		"bright" colors that look better, or the more widely supported 
		standard ones. 
		
		Called during startup, but can also be programatically invoked 
		later 
		
		:param bright: set to False to force only the basic (30-39) codes 
			or True to use the better-looking 90-99 bright codes which are not 
			supported by all terminals. Default is bright=False, but can be 
			overridden by the ``PYSYS_COLOR_BASIC`` environment var. 
		"""
		if bright is None: bright = os.getenv('PYSYS_COLOR_BRIGHT','true')=='true'
		# by default we use standard ANSI escape sequences, supported by most unix terminals
		ColorLogFormatter.COLOR_ESCAPE_CODES = {
			'BLACK':   '\033[%dm' % (30 if not bright else 90),
			'RED':     '\033[%dm' % (31 if not bright else 91),
			'GREEN':   '\033[%dm' % (32 if not bright else 92),
			'YELLOW':  '\033[%dm' % (33 if not bright else 93),
			'BLUE':    '\033[%dm' % (34 if not bright else 94),
			'MAGENTA': '\033[%dm' % (35 if not bright else 95),
			'CYAN':    '\033[%dm' % (36 if not bright else 96),
			'WHITE':   '\033[%dm' % (37 if not bright else 97),
			'END':     '\033[%dm' % (0),
		}

	__STDOUT_LOCK = threading.Lock() # global lock shared by all instances of this class

	def __init__(self, propertiesDict):
		"""Create an instance of the formatter class."""

		# extract to override entries in the color map from properties
		for prop in list(propertiesDict.keys()):
			if prop.startswith('color:'):
				self.COLOR_CATEGORIES[prop[len('color:'):].lower()] = propertiesDict.pop(prop).upper()

		self.color = None
		if 'color' in propertiesDict:
			self.color = propertiesDict.pop('color','').lower() == 'true'
		# env vars should take precedence over project settings
		if os.getenv('NO_COLOR',''):
			self.color = False # this is a growing cross-product standard way to disable color
		if os.getenv('PYSYS_COLOR',None):
			self.color = os.getenv('PYSYS_COLOR').lower() == 'true'

		if self.color is None: 
			# heuristically decide on an appropriate default if not configured in the project
			if not sys.__stdout__.isatty():
				self.color = False
			elif not IS_WINDOWS: # most unix terminals will support coloring
				self.color = True
			else:
				try:
					import colorama
				except Exception:
					self.color = False
				else:
					self.color = True
		
		if self.color: 
			# initColoringLibrary, which might result in sys.stdout getting rewritten; PySys needs control of sys.stdout 
			# so capture the new stdout then restore the original
			with ColorLogFormatter.__STDOUT_LOCK:
				stdoutbak = sys.stdout
				try:
					sys.stdout = sys.__stdout__
					self.initColoringLibrary()
				finally:
					updatedstdout = sys.stdout
					sys.stdout = stdoutbak
				# now update the stream used by our handler
				if 'PySysPrintRedirector' in repr(updatedstdout):
					raise Exception('Formatter has redirector: %s'%repr(updatedstdout))

				stdoutHandler.stream.updateUnderlyingStream(updatedstdout)

		super(ColorLogFormatter, self).__init__(propertiesDict)

		# ensure all outcomes are permitted as possible precedents		
		for outcome in OUTCOMES:
			if str(outcome).lower() not in self.COLOR_CATEGORIES:
				self.COLOR_CATEGORIES[str(outcome).lower()] = self.COLOR_CATEGORIES[LOG_FAILURES] if outcome.isFailure() else self.COLOR_CATEGORIES[LOG_PASSES]
		for cat in self.COLOR_CATEGORIES: assert self.COLOR_CATEGORIES[cat] in self.COLOR_ESCAPE_CODES, cat


	def formatException(self, exc_info):
		"""Format an exception for logging, returning the new value.

		:param exc_info: The exception info
		:return: The formatted message ready for logging

		"""
		msg = super(ColorLogFormatter, self).formatException(exc_info)
		if self.color:
			return self.colorCategoryToEscapeSequence(LOG_TRACEBACK)+ msg + \
				self.colorCategoryToEscapeSequence(LOG_END)
		else:
			return msg


	def format(self, record):
		"""Format a log record for logging, returning the new value.

		:param record: The message to be formatted
		:return: The formatted message ready for logging

		"""
		if self.color:
			try:
				cat = getattr(record, self.CATEGORY, None)
				if not cat:
					if record.levelname == 'WARN': cat = LOG_WARN
					elif record.levelname == 'ERROR': cat = LOG_ERROR
					elif record.levelname == 'DEBUG': cat = LOG_DEBUG
				if cat:
					cat = cat.lower()
					record = copy.copy(record)
					indexes = getattr(record, self.ARG_INDEX, None)
					if indexes == None:
						record.msg = self.colorCategoryToEscapeSequence(cat)+record.msg+self.colorCategoryToEscapeSequence(LOG_END)
					else:
						args = list(record.args)
						for index in indexes: args[index] = self.formatArg(cat, args[index])
						record.args = tuple(args)
					
			except Exception as e:
				logging.getLogger('pysys.utils.logutils').debug('Failed to format log message "%s": %s'%(record.msg, repr(e)))

		return super(ColorLogFormatter, self).format(record)


	def formatArg(self, category, arg):
		"""Format a single argument within a record, based on its category.

		:param category: The logging category
		:param arg: The argument within the record.

		"""
		if isstring(arg): return self.colorCategoryToEscapeSequence(category)+arg+self.colorCategoryToEscapeSequence(LOG_END)
		return arg


	def colorCategoryToEscapeSequence(self, category):
		""" Return the escape sequence to be used for the specified category of logging output. 
		
		:param category: The category of the log message
		:return: The escape sequence

		"""
		color = self.COLOR_CATEGORIES.get(category, '<%s>'%category)
		return self.COLOR_ESCAPE_CODES.get(color.upper(), '<%s>'%color)


	def initColoringLibrary(self):
		"""Initialize any python library required for ensuring ANSI escape sequences can be processed.

		The default implementation does nothing on Unix but on Windows attempts to load the "Colorama"
		library if is is present (unless the environment variable 
		PYSYS_DISABLE_COLORAMA=true is set).

		"""
		if OSFAMILY=='windows' and os.getenv('PYSYS_DISABLE_COLORAMA','')!='true':
			try:
				import colorama
				colorama.init()
				logging.getLogger('pysys.utils.logutils').debug('Successfully initialized the coloring library')
			except Exception as e:
				logging.getLogger('pysys.utils.logutils').debug('Failed to load coloring library: %s', repr(e))
ColorLogFormatter.configureANSIEscapeCodes()

def stdoutPrint(s):
	"""
	Writes the specified bytes or (preferably) unicode character string 
	to stdout, avoiding any redirection to loggers performed by PySys, and 
	performing replacements if needed based on the characters 
	supported by the stdout encoding, and with support for output coloring 
	using escape sequences (if enabled in PySys). 

	In most cases a logger should be used for output from PySys, but this 
	function is provided as a way to write to stdout for cases where it is truly 
	needed, such as unconditionally writing status messages to a CI system. 
	
	:param s: a unicode or bytes string. A newline will be added automatically. 
	"""
	if isinstance(s, binary_type):
		s += b'\n'
	else:
		s += u'\n'
	return stdoutHandler.stream.write(s)
