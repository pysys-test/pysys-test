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

import logging, time, urlparse, os, stat

from pysys.constants import *
from pysys.exceptions import *

from xml.dom.minidom import getDOMImplementation

class BasePySysLoggingFormatter(logging.Formatter):
	"""
	Base class for formatting for log messages, either destined for the stdout/console 
	or for the run.log file. 
	
	The default implementation delegates everything to L{logging.Formatter} using 
	the configured messagefmt and datefmt. 
	
	Subclasses may be implemented to provide any required customizations, and 
	can be registered by specifying classname= and module= in the formatter node 
	of the project configuration file. 
	"""
	def __init__(self, optionsDict, isStdOut):
		"""
		Constructs a formatter. 
		
		@param optionsDict: dictionary of formatter-specific options which can be customized; 
		these are configured by providing attributes on the formatter node of the 
		project configuration file. 
		Any options handled by a subclass should be removed (popped) before passing the 
		remaining optionsDict to the super class, which will throw an exception 
		if any unexpected options are present. 
		
		@param isStdOut: True if this formatter is producing output for stdout i.e. the console. 
		"""
		self.isStdOut = isStdOut
		super(BasePySysLoggingFormatter, self).__init__(
			optionsDict.pop('messagefmt', DEFAULT_FORMAT_STDOUT if isStdOut else DEFAULT_FORMAT_RUNLOG),
			optionsDict.pop('datefmt', None)
			)
		
		if optionsDict: raise Exception('Unknown formatter option(s) specified: %s'%', '.join(optionsDict.keys()))
	
class DefaultPySysLoggingFormatter(BasePySysLoggingFormatter):
	"""
	The default formatter for creating log messages. 
	"""
	pass