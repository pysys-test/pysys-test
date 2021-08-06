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
Exceptions used and raised by PySys methods. 

"""

from pysys.constants import TIMEDOUT

class AbortExecution(Exception):
	"""Raised to abort execution of a test."""

	def __init__(self, outcome, outcomeReason, callRecord=None):
		self.outcome, self.value, self.callRecord = outcome, outcomeReason, callRecord
		
	def __str__(self):
		return self.value

class FileNotFoundException(Exception):
	"""Exception raised when a file cannot be found."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class IncorrectFileTypeException(Exception):
	"""Exception raised when the extension of a file is incorrect."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class ExecutableNotFoundException(Exception):
	"""Exception raised when an executable cannot be found."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class ProcessError(Exception):
	"""Exception raised when creating a process."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class ProcessTimeout(AbortExecution):
	"""Exception raised when a process times out."""

	def __init__(self,value):
		super(ProcessTimeout, self).__init__(TIMEDOUT, value)

class InvalidDescriptorException(Exception):
	"""Exception raised when a testcase descriptor is invalid."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class InvalidXMLException(Exception):
	"""Exception raised when an input XML file is invalid."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class UserError(Exception):
	"""Exception raised when the user has made a mistake, for example 
	specifying a wrong value or providing an invalid file.
	
	This exception should be raised with a user-friendly error message, 
	and indicates that there is no need to display a Python stack trace.
	Do not use this exception type for non-user errors, in which case a stack 
	trace could be important for debugging the problem. 
	"""

	def __init__(self, message):
		super(UserError, self).__init__(message)
	