#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018 M.B.Grieve

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

import logging, time, os, copy

from pysys.constants import *
from pysys.exceptions import *

class BasePySysLoggingFormatter(logging.Formatter):
	"""
	Base class for formatting for log messages, either destined for the stdout/console 
	or for the run.log file. 
	
	The default implementation delegates everything to L{logging.Formatter} using 
	the configured messagefmt and datefmt. 
	
	Subclasses may be implemented to provide any required customizations, and 
	can be registered by specifying classname= in the formatter node 
	of the project configuration file. 
	"""
	def __init__(self, propertiesDict, isStdOut):
		"""
		Constructs a formatter. 
		
		@param propertiesDict: dictionary of formatter-specific options which can be customized; 
		these are configured by providing <property name="..." value="..."/> elements or attributes 
		on the formatter node of the project configuration file. 
		Any properties handled by a subclass should be removed (popped) before passing the 
		remaining propertiesDict to the super class, which will throw an exception 
		if any unexpected options are present. 
		
		@param isStdOut: True if this formatter is producing output for stdout i.e. the console. 
		Some formatters may treat console output differently to output to a file. 
		"""
		self.isStdOut = isStdOut
		super(BasePySysLoggingFormatter, self).__init__(
			propertiesDict.pop('messagefmt', DEFAULT_FORMAT_STDOUT if isStdOut else DEFAULT_FORMAT_RUNLOG),
			propertiesDict.pop('datefmt', None)
			)
		
		if propertiesDict: raise Exception('Unknown formatter option(s) specified: %s'%', '.join(propertiesDict.keys()))
	
class DefaultPySysLoggingFormatter(BasePySysLoggingFormatter):
	"""
	The default formatter for creating log messages. 
	
	Supports coloring the console output if PYSYS_COLOR=true environment 
	variable is set, or the "color" option is set to true on the formatter. 
	The colors used for each colorable category defined by this class 
	can be overridden by specifying "color:XXX" options, e.g. 
	<formatter><property name="color:dumped core" value="YELLOW"/></formatter>
	"""
	
	KEY_COLOR_CATEGORY = 'pysys_color_category' # the key to add to the extra={} dict of a logger call to specify what kind of color to give it
	KEY_COLOR_ARG_INDEX = 'pysys_color_arg_index' # the key to add to the extra={} dict of a logger call to color the specified formatted arg rather than the whole message
	
	# we don't want to hardcode the specific colors in the various places where we log stuff, so 
	# use a lookup table here to map from colorable message "categories" to colors, 
	# which can be overridden in configuration or a subclass. 
	# All other outcomes not explicitly listed here are colored as "passed" or "failed"
	COLOR_CATEGORIES = {
		'warn':'MAGENTA',
		'error':'RED',
		'traceback':'RED',
		'debug':'BLUE', # blue lines blend into black well, and highlighting debug lines makes it easier to read the non-debug lines
		'filecontents':'BLUE', # these are effectively debug lines
		'details':'CYAN', # details such as test id that are worth highlighting
		'outcomereason':'CYAN', # this is key info so make it stand out in a different color
		
		# pick colors to make it easy to see at a glance whether it passed/failed/skipped; 
		# timedout often indicates a loaded machine or mis-sized test so merits a distinct color
		'timed out':'MAGENTA',
		'failed':'RED',
		'passed':'GREEN',
		'skipped':'YELLOW',
		
		'end':'END',
	}
	
	# By default we use standard ANSI escape sequences, supported by most unix terminals 
	# and several libraries for windows too. Can be customized by a subclass if desired
	COLOR_ESCAPE_CODES = {
		'BLUE': '\033[94m',
		'GREEN':'\033[92m',
		'YELLOW':'\033[93m',
		'RED':'\033[91m',
		'MAGENTA':'\033[95m',
		'CYAN':'\033[96m',
		'WHITE':'\033[97m',
		'END':'\033[0m',
	}
	
	def __init__(self, propertiesDict, isStdOut):
		# whether to color console output should usually be configured in the environment 
		# rather than the pysys project, since it depends on the preference of the 
		# person running the tests, and to what OS and shell/terminal type they are using
		
		# allow color:XXX prefixes to specify the color for particular categories
		for o in list(propertiesDict.keys()):
			if o.startswith('color:'):
				self.COLOR_CATEGORIES[o[len('color:'):].lower()] = propertiesDict.pop(o).upper()
		
		self.color = propertiesDict.pop('color','')=='true'
		self.color = isStdOut and (os.getenv('PYSYS_COLOR', 'false').lower() == 'true' or self.color)
		if self.color: self.initColoringLibrary()
		super(DefaultPySysLoggingFormatter, self).__init__(propertiesDict, isStdOut)

		# ensure all outcomes are permitted as possible precedents		
		for outcome in PRECEDENT:
			if LOOKUP[outcome].lower() not in self.COLOR_CATEGORIES:
				self.COLOR_CATEGORIES[LOOKUP[outcome].lower()] = self.COLOR_CATEGORIES['failed'] if outcome in FAILS else self.COLOR_CATEGORIES['passed']
		for cat in self.COLOR_CATEGORIES: assert self.COLOR_CATEGORIES[cat] in self.COLOR_ESCAPE_CODES, cat

	def formatException(self, exc_info):
		# override standard formatter to add coloring
		return self.colorCategoryToEscapeSequence('traceback')+super(DefaultPySysLoggingFormatter, self).formatException(exc_info)+self.colorCategoryToEscapeSequence('end')

	def format(self, record):
		# override standard formatter to add coloring
		if self.color:
			try:
				cat = getattr(record, self.KEY_COLOR_CATEGORY, None)
				if not cat:
					# if no category was explicitly specified, color warn and error lines
					if record.levelname == 'WARN':
						cat = 'warn'
					elif record.levelname == 'ERROR':
						cat = 'error'
					elif record.levelname == 'DEBUG':
						cat = 'debug'
				if cat: # if there's something to color
					cat = cat.lower()
					record = copy.copy(record)
					i = getattr(record, self.KEY_COLOR_ARG_INDEX, None)
					if i == None or not isinstance(record.args[i], str): # color whole line
						record.msg = self.colorCategoryToEscapeSequence(cat)+record.msg+self.colorCategoryToEscapeSequence('end')
					else:
						args = list(record.args)
						args[i] = self.colorCategoryToEscapeSequence(cat)+args[i]+self.colorCategoryToEscapeSequence('end')
						record.args = tuple(args)
					
			except Exception as e:
				log.debug('Failed to format log message "%s": %s'%(record.msg, repr(e)))
		return super(DefaultPySysLoggingFormatter, self).format(record)
	
	def colorCategoryToEscapeSequence(self, category):
		""" Return the escape sequence to be used for the specified category of logging output. 
		
		@param category: A colorable category such as 'passed' or 'warn'. In the default implementation 
		of this class, categories should be in self.COLOR_CATEGORIES
		@return: The escape sequence.  
		"""
		color = self.COLOR_CATEGORIES.get(category, '<%s>'%category)
		return self.COLOR_ESCAPE_CODES.get(color.upper(), '<%s>'%color)
	
	def initColoringLibrary(self):
		"""
		Initialize any python library required for ensuring ANSI escape sequences 
		can be processed, e.g. for terminals such as Windows that do not do this 
		automatically. The default implementation does nothing on Unix but on Windows 
		attempts to load the "Colorama" library if is is present. 
		"""
		if OSFAMILY=='windows':
			try:
				# if user happens to have the colorama library installed, try to load it since 
				# then we get coloring for free. If not, no harm done. User could provide 
				# a subclass that loads a different library if desired. 
				import colorama
				colorama.init()
			except Exception as e:
				logging.getLogger('pysys.utils.logutils').debug('Failed to load coloring library: %s', repr(e))
			
		# since sys.stdout may be been redirected using the above, we need to change the 
		# stream that our handler points at
		assert stdoutHandler.stream # before we change it make sure it's currently set
		stdoutHandler.stream = sys.stdout
			