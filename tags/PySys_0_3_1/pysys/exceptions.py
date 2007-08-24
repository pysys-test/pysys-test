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
# dealings in the software


class FileNotFoundException:
	"""Exception raised when a file cannot be found."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value


class IncorrectFileTypeException:
	"""Exception raised when the extension of a file is incorrect."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value


class ExecutableNotFoundException:
	"""Exception raised when an executable cannot be found."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class ProcessError:
	"""Exception raised when creating a process."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class ProcessTimeout:
	"""Exception raised when a process times out."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class InvalidDescriptorException:
	"""Exception raised when a testcase descriptor is invalid."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value

class InvalidXMLException:
	"""Exception raised when an input XML file is invalid."""

	def __init__(self,value):
		self.value=value
		
	def __str__(self):
		return self.value
