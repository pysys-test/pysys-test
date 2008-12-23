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
__all__ = [ "createDescriptors",
			"console" ]

import sys, os, os.path, glob, getopt, sets, re, string, logging

from pysys import log
from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.descriptor import XMLDescriptorParser


def createDescriptors(testIdSpecs, type, includes, excludes, trace, dir=None):
	"""Create a list of descriptor objects representing a set of tests to run, returning the list.
	
	@param testIdSpecs: A string specifier for a set of testcase identifiers
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
	ignoreSet = sets.Set(OSWALK_IGNORES)
	descriptorSet = sets.Set(DEFAULT_DESCRIPTOR)
	
	if dir == None: dir = os.getcwd()
	for root, dirs, files in os.walk(dir):
		intersection =  descriptorSet & sets.Set(files)
		if intersection : descriptorfiles.append(os.path.join(root, intersection.pop()))
		for ignore in (ignoreSet & sets.Set(dirs)): dirs.remove(ignore)

	for descriptorfile in descriptorfiles:
		try:
			descriptors.append(XMLDescriptorParser(descriptorfile).getContainer())
		except Exception, value:
			print sys.exc_info()[0], sys.exc_info()[1]
			log.info("Error reading descriptorfile %s" % descriptorfile)
	descriptors.sort(lambda x, y: cmp(x.file, y.file))

	# trim down the list for those tests in the test specifiers 
	tests = []
	if testIdSpecs == []:
		tests = descriptors
	else:
		for testIdSpec in testIdSpecs:
			try:	
				if re.search('^[\w_]*$', testIdSpec):
					for i in range(0,len(descriptors)):
						if descriptors[i].id == testIdSpec: index = i
					tests.extend(descriptors[index:index+1])
				elif re.search('^:[\w_]*', testIdSpec):
					for i in range(0,len(descriptors)):
						if descriptors[i].id == string.split(testIdSpec, ':')[1]: index = i
					tests.extend(descriptors[:index+1])

				elif re.search('^[\w_]*:$', testIdSpec):
					for i in range(0,len(descriptors)):
					  	if descriptors[i].id == string.split(testIdSpec, ':')[0]: index = i
					tests.extend(descriptors[index:])

				elif re.search('^[\w_]*:[\w_]*$', testIdSpec):
					for i in range(0,len(descriptors)):
					  	if descriptors[i].id == string.split(testIdSpec, ':')[0]: index1 = i
					  	if descriptors[i].id == string.split(testIdSpec, ':')[1]: index2 = i
					tests.extend(descriptors[index1:index2+1])
			except :
				raise Exception("Unable to locate requested testcase(s)")
				
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
		raise Exception("The supplied options did not result in the selection of any tests")
	else:
		return tests
		

