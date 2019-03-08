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

import sys, os, io, locale

"""
@undocumented: PY2, binary_type, _UnicodeSafeStreamWrapper
"""

PY2 = sys.version_info[0] == 2
binary_type = str if PY2 else bytes

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
		@param underlying: the underlying stream. May optionally have an "encoding" field. 
		@param writebytes: if True, bytes are written, if False unicode characters are written. 
		@param encoding: encoding which all written bytes/chars are guaranteed to be present in; 
		if None, will be taken from underlying encoding or getpreferredencoding(). 
		"""
		self.stream = underlying
		# on python 2 stdout.encoding=None if redirected, and falling back on getpreferredencoding is the best we can do
		self.__encoding = encoding or getattr(underlying, 'encoding', None) or locale.getpreferredencoding()
		assert self.__encoding
		self.__writebytes = writebytes
	
	def write(self, s):
		if not s: return
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
				
	def flush(self): 
		if self.stream is None: return
		self.stream.flush()
	
	def close(self): 
		"""
		Flush and close the stream, and prevent any more writes to it. 
		This method is idempotent. 
		"""
		if self.stream is None: return
		self.stream.flush()
		self.stream.close()
		self.stream = None
