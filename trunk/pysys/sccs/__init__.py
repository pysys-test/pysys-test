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
"""
Contains implementations of wrappers around source code control systems.  

Configuration of PySys allows specification of the source code control system (sccs) being used 
for the revision control of projects, e.g. svn, cvs etc. Different sccs have an implementation 
of the SCCSInterface to perform generic operations such as returning a label to denote the revision 
identifier of a local working copy checked out from the sccs, or to update the local working 
directory tree at a certain point within the tree etc. At the moment this is a very simple 
interface for use within continuous integration, e.g. where cycles of tests are performed when an 
update on the revision identifier is seen.

"""
__all__ = [ "SCCSInterface",
		    "SCCSsvn" ]

import os, sys
from xml.dom.minidom import getDOMImplementation
from xml.dom.minidom import parseString

from pysys import log

class SCCSInterface:
	"""Defines the generic interface for source code control operations used within PySys. 

	"""
	
	def __init__(self, **kwargs):
		"""Class constructor.
	
	 	@param kwargs: Keyword arguments to allow for extension of the interface

		"""
		pass
	
	def getLabel(self, path, **kwargs):
	 	"""Return a label denoting a revision identifier of a local working copy.
	 	
	 	@param path: Full path within the local working copy to obtain the label from.
	 	@param kwargs: Keyword arguments to allow for extension of the interface
	 	
	 	"""
	 	pass
	 
	def isNewerLabel(self, current, previous):
		"""Return true if the current label indicates an update compared to the previous label.
		
		@param current: The current label to use in the comparison
		@param previous: The previous label to use in the comparison
	 	@param kwargs: Keyword arguments to allow for extension of the interface
	 	
		"""
		pass
	 
	def update(self, path, label=None, **kwargs):
		"""Perform an update of a local working copy located at a point within the directory tree. 
	 	
	 	@param path: Full path within the local working copy to update
	 	@param path: The label to update to e.g. the head of the repository 
	 	@param kwargs: Keyword arguments to allow for extension of the interface
	 	
	 	"""
	 	pass


class SCCSsvn:
	"""Implementation of the generic interface for source code control operations for Subversion. 

	This implementation of the SVN SCCS class assumes the client svn executable is installed on the 
	host machine. This client is then used to perform operations to obtain the label from a given 
	path, and to update a working copy etc. Note that whilst pysvn could have been used, no distribution
	bundles exists at the moment for unix systems. 

	@ivar bindir: The directory containing the svn client executable
	@type mode: string
	
	"""
	bindir = None
	
	def __init__(self, **kwargs):
		"""Class constructor.
	
	 	@param kwargs: Keyword arguments for extending classes

		"""
		if self.bindir == None:
			raise Exception, "No svn client binary directory specified"
		
		if not os.path.exists(self.bindir):
			 raise Exception, "Specified binary directory does not exist %s" % (self.bindir)	
	
	
	def getLabel(self, path, **kwargs):
	 	"""Return a label denoting a revision identifier of a local working copy.
	 	
	 	@param path: Full path within the local working copy to obtain the label from.
	 	@param kwargs: Keyword arguments for extending classes
	 	
	 	"""
	 	if not os.path.exists(path):
			 raise Exception, "Requested path does not exist %s" % (path)

		info = ''	
	 	cwd = os.getcwd()
	 	out = os.popen("%s info --xml" % os.path.join(self.bindir, 'svn'))
		for line in out.readlines(): info=info+line
		out.close()
		os.chdir(cwd)
		
		dom = parseString(info)
		infoElement = dom.getElementsByTagName('info')[0]
		entryElement = infoElement.getElementsByTagName('entry')[0]			
		commitElement = entryElement.getElementsByTagName('commit')[0]		
		return commitElement.getAttribute('revision')
	
	 
	def isNewerLabel(self, current, previous):
		"""Return true if the current label indicates an update compared to the previous label.
		
		@param current: The current label to use in the comparison
		@param previous: The previous label to use in the comparison
	 	@param kwargs: Keyword arguments for extending classes
	 	
		"""
		pass
	
	 
	def update(self, path, label=None, **kwargs):
		"""Perform an update of a local working copy located at a point within the directory tree. 
	 	
	 	@param path: Full path within the local working copy to update
	 	@param path: The label to update to e.g. the head of the repository 
	 	@param kwargs: Keyword arguments for extending classes
	 	
	 	"""
	 	pass
