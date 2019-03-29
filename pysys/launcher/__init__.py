#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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
Contains utilities used by test launchers when running, printing, cleaning or making new tests. 

The module includes the L{pysys.launcher.createDescriptors} method which locates test 
descriptors based upon a given starting location on the file system, the chosen range 
of test ids, the test type, the specified requirements, and the include and exclude lists.

Utilities defined in the module can be used by any launchers, either distributed
with the framework, or created as an extension to it. Currently the framework 
distributes the console launcher module only - see L{pysys.launcher.console}. This 
module uses the current working directory in a command shell as the starting location 
on the file system, and provides utilities for parsing command line arguments in order
to launch operations against a set of tests etc.  

"""
from __future__ import print_function
__all__ = [ "createDescriptors","console" ]

import os.path, logging
import locale

# if set is not available (>python 2.6) fall back to the sets module
try:  
	set  
except NameError:  
	import sets
	from sets import Set as set

from pysys.constants import *
from pysys.xml.descriptor import XMLDescriptorParser
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe
from pysys.utils.pycompat import PY2

def createDescriptors(testIdSpecs, type, includes, excludes, trace, dir=None):
	"""Create a list of descriptor objects representing a set of tests to run, returning the list.
	
	@param testIdSpecs: A list of strings specifying the set of testcase identifiers
	@param type: The type of the tests to run (manual | auto)
	@param includes: A list of test groups to include in the returned set
	@param excludes: A list of test groups to exclude in the returned set
	@param trace: A list of requirements to indicate tests to include in the returned set
	@param dir: The parent directory to search for runnable tests
	@return: List of L{pysys.xml.descriptor.XMLDescriptorContainer} objects
	@rtype: list
	@raises Exception: Raised if not testcases can be found or are returned by the requested input parameters
	
	"""
	descriptors = []
	descriptorfiles = []
	ignoreSet = set(OSWALK_IGNORES)
	descriptorSet =set(DEFAULT_DESCRIPTOR)
	
	if dir is None: dir = os.getcwd()
	projectfound = PROJECT.projectFile != None
	
	# although it's highly unlikely, if any test paths did slip outside the Windows 256 char limit, 
	# it would be very dangerous to skip them (which is what os.walk does unless passed a \\?\ path). 
	i18n_reencode = locale.getpreferredencoding() if PY2 and isinstance(dir, str) else None
	for root, dirs, files in os.walk(toLongPathSafe(dir)):
		intersection =  descriptorSet & set(files)
		if intersection: 
			descriptorpath = fromLongPathSafe(os.path.join(root, intersection.pop()))
			# PY2 gets messed up if we start passing unicode rather than byte str objects here, 
			# as it proliferates to all strings in each test
			if i18n_reencode is not None: descriptorpath = descriptorpath.encode(i18n_reencode) 
			descriptorfiles.append(descriptorpath)
		
		for ignore in (ignoreSet & set(dirs)): dirs.remove(ignore)
		if not projectfound:
			for p in DEFAULT_PROJECTFILE:
				if p in files:
					projectfound = True
					sys.stderr.write('WARNING: PySys project file was not found in directory the script was run from but does exist at "%s" (consider running pysys from that directory instead)\n'%os.path.join(root, p))

	for descriptorfile in descriptorfiles:
		try:
			descriptors.append(XMLDescriptorParser(descriptorfile).getContainer())
		except Exception as value:
			print('%s - %s'%(sys.exc_info()[0], sys.exc_info()[1]))
			logging.getLogger('pysys').info("Error reading descriptorfile %s" % descriptorfile)
	descriptors = sorted(descriptors, key=lambda x: x.file)

	# trim down the list for those tests in the test specifiers 
	tests = []
	if testIdSpecs == []:
		tests = descriptors
	else:
		def idMatch(descriptorId, specId):
			return specId==descriptorId or (specId.isdigit() and re.match('.+_0*%s$'%specId, descriptorId))

		for t in testIdSpecs:
			try:
				index = index1 = index2 = -1
				t = t.rstrip('/\\')

				if re.search('^[\w_]*$', t):
					for i in range(0,len(descriptors)):
						if idMatch(descriptors[i].id, t): index = i
					matches = descriptors[index:index+1]

				elif re.search('^:[\w_]*', t):
					for i in range(0,len(descriptors)):
						if idMatch(descriptors[i].id, t.split(':')[1]): index = i
					matches = descriptors[:index+1]

				elif re.search('^[\w_]*:$', t):
					for i in range(0,len(descriptors)):
					  	if idMatch(descriptors[i].id, t.split(':')[0]): index = i
					matches = descriptors[index:]

				elif re.search('^[\w_]*:[\w_]*$', t):
					for i in range(0,len(descriptors)):
					  	if idMatch(descriptors[i].id, t.split(':')[0]): index1 = i
					  	if idMatch(descriptors[i].id, t.split(':')[1]): index2 = i
					matches = descriptors[index1:index2+1]

				else:
					matches = [descriptors[i] for i in range(0,len(descriptors)) if re.search(t, descriptors[i].id)]

				# each specified test patten must match something, else probably user made a typo
				if not matches: raise Exception("No matches for: '%s'", t)
				tests.extend(matches)

			except Exception:
				sys.exit("Unable to locate requested testcase(s): '%s'"%t)

				
	# trim down the list based on the type
	if type:
		index = 0
		while index != len(tests):
			if type != tests[index].type:
				tests.pop(index)
			else:
				index = index + 1
			
	# trim down the list based on the include and exclude groups
	if len(excludes) != 0:
		index = 0
		while index != len(tests):
			remove = False

			for exclude in excludes:
				if exclude in tests[index].groups:
					remove = True
					break

			if remove:
				tests.pop(index)
			else:
				index = index +1
				
	if includes != []:
		index = 0
		while index != len(tests):
			keep = False
				
			for include in includes:
				if include in tests[index].groups:
					keep = True
					break

			if not keep:
				tests.pop(index)
			else:
				index = index +1

	# trim down the list based on the traceability
	if trace:
		index = 0
		while index != len(tests):
			if trace not in tests[index].traceability :
				tests.pop(index)
			else:
				index = index + 1
	
	if len(tests) == 0:
		sys.exit("The supplied options did not result in the selection of any tests")
	else:
		return tests


