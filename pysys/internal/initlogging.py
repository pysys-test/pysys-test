#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B.Grieve

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

# Contains internal (non-API) utilities for initializing logging

import sys, os, io, locale, logging, threading

# must not import any pysys packages here, as this module's code needs to execute first

binary_type = bytes

_PREFERRED_ENCODING = locale.getpreferredencoding() # also exists in pysys.constants.

class _UnicodeSafeStreamWrapper(object):
	"""
	Non-public API - for internal use only, may change at any time. 
	
	Wraps a stream, forwarding calls to flush()/close() and ensuring all 
	write() calls are forwarded with either unicode or byte strings 
	(depending on the writebytes argument) but not a mixture, with conversions 
	performed safely replacing invalid characters rather than generating exceptions. 
	
	There is no __del__ implementation to automatically close the stream, 
	to faciliate having multiple wrappers using the same underlying stream. 
	"""
	def __init__(self, underlying, writebytes, encoding=None):
		"""
		:param underlying: the underlying stream. May optionally have an "encoding" field. 
		:param writebytes: if True, bytes are written, if False unicode characters are written. 
		:param encoding: encoding which all written bytes/chars are guaranteed to be present in; 
		if None, will be taken from underlying encoding or getpreferredencoding(). 
		"""
		self.__writebytes = writebytes
		self.__requestedEncoding = encoding
		self.updateUnderlyingStream(underlying)
	
	def updateUnderlyingStream(self, underlying):
		assert underlying != self # avoid infinite loops
		self.stream = underlying
		# on python 2 stdout.encoding=None if redirected, and falling back on getpreferredencoding is the best we can do
		self.__encoding = self.__requestedEncoding or getattr(underlying, 'encoding', None) or _PREFERRED_ENCODING
		assert self.__encoding
	
	def write(self, s):
		if not s: return
		try:
			if self.__writebytes:
				if isinstance(s, binary_type):
					self.stream.write(s) # always safe in python 2 and not supported in python 3
				else:
					self.stream.write(s.encode(self.__encoding, errors='replace'))
			else:
				if isinstance(s, binary_type):
					s = s.decode(self.__encoding, errors='replace')
				# even if it's already a unicode string it could contain characters that aren't supported in this encoding 
				# (e.g. unicode replacement characters - such as the decode above generates - aren't supported by ascii); 
				# so check it round-trips
				s = s.encode(self.__encoding, errors='replace')
				s = s.decode(self.__encoding, errors='replace')
				self.stream.write(s)
		except Exception:
			if self.stream is None: # it was closed underneath us
				pass
			else:
				raise
				
	def flush(self): 
		if self.stream is None: return
		self.stream.flush()
	
	def close(self): 
		"""
		Flush and close the stream, and prevent any more writes to it. 
		This method is idempotent. 
		"""
		stream, self.stream = self.stream, None
		
		if stream is None: return
		stream.flush()
		stream.close()

class DelegatingPerThreadLogHandler(logging.Handler):
	"""A log handler that delegates emits to a list of handlers, 
	set on a per-thread basis. If no handlers are setup for this 
	thread nothing is emitted.
	
	Note that calling close() on this handler does not call close 
	on any of the delegated handlers (since they may 
	be used by multiple threads, and to avoid leaks we don't keep a 
	global list of them anyway). 
	"""
	def __init__(self):
		super(DelegatingPerThreadLogHandler, self).__init__()
		self.__threadLocals = threading.local()

	def setLogHandlersForCurrentThread(self, handlers):
		self.__threadLocals.handlers = handlers
		self.__threadLocals.emitFunctions = [(h.level, h.emit) for h in handlers] if handlers else None

	def getLogHandlersForCurrentThread(self):
		return getattr(self.__threadLocals, 'handlers', None) or []
	
	def emit(self, record):
		functions = getattr(self.__threadLocals, 'emitFunctions', None) 
		if functions is not None: 
			for (hdlrlevel, emitFunction) in functions:
				# handlers can have different levels, so need to replicate the checking that callHandlers performs
				if record.levelno >= hdlrlevel:
					emitFunction(record)
	def flush(self): 
		for h in self.getLogHandlersForCurrentThread(): h.flush()

class ThreadFilter(logging.Filterer):
	"""Filter to disallow log records from the current thread.
	
	Deprecated. 
	
	Within pysys, logging to standard output is only enabled from the main thread 
	of execution (that in which the test runner class executes). When running with
	more than one test worker thread, logging to file of the test run log is 
	performed through a file handler, which only allows logging from that thread. 
	To disable either of these, use an instance of this class from the thread in 
	question, adding to the root logger via log.addFilter(ThreadFilter()).
	
	"""
	def __init__(self):
		"""Overrides logging.Filterer.__init__"""
		self.threadId = threading.current_thread().ident
		logging.Filterer.__init__(self)
		
	def filter(self, record):
		"""Implementation of logging.Filterer.filter to block from the creating thread."""
		if self.threadId != threading.current_thread().ident: return True
		return False

#####################################

# Initialize Python logging for PySys

# avoids a bug where error handlers using the Python root handler could mess up 
# subsequent logging if no handlers are defined
logging.getLogger().addHandler(logging.NullHandler())

rootLogger = logging.getLogger('pysys')
"""The root logger for logging within PySys."""

log = rootLogger

stdoutHandler = logging.StreamHandler(_UnicodeSafeStreamWrapper(sys.stdout, writebytes=False))
"""The handler that sends pysys.* log output from to stdout, 
including buffered output from completed tests when running in parallel.

The .stream field can be used to access the wrapper we use throughout 
pysys to safely write to stdout (with coloring support if enabled). 
"""

pysysLogHandler = DelegatingPerThreadLogHandler()
""" The log handler used by PySys. It ignores log messages unless 
setLogHandlersForCurrentThread has been called on the current thread. 
"""

# customize the default logging names for display
logging.addLevelName(50, 'CRIT')
logging.addLevelName(30, 'WARN')
stdoutHandler.setLevel(logging.DEBUG) # Needs to be debug otherwise we can't change the log level down 
stdoutHandler.setFormatter(logging.Formatter('%(levelname)s %(message)s')) # formatter to use for any debug/error messages, just until we load the project file
rootLogger.setLevel(logging.INFO) # The default root logger log level 
rootLogger.addHandler(pysysLogHandler)
pysysLogHandler.setLogHandlersForCurrentThread([stdoutHandler]) # main thread is by default the only one that writes to stdout

