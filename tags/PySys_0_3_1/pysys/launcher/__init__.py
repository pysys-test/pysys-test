__all__ = [ "createDescriptors",
			"console" ]

import sys, os, os.path, glob, getopt, sets, re, string, logging

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.descriptor import XMLDescriptorParser

log = logging.getLogger('pysys.launcher')
log.setLevel(logging.NOTSET)


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
	if dir == None: dir = os.getcwd()
	for root, dirs, files in os.walk(dir):
		if DEFAULT_DESCRIPTOR in files: descriptorfiles.append(os.path.join(root, DEFAULT_DESCRIPTOR))
		for ignore in (ignoreSet & sets.Set(dirs)): dirs.remove(ignore)

	for descriptorfile in descriptorfiles:
		try:
			descriptors.append(XMLDescriptorParser(descriptorfile).getContainer())
		except Exception, value:
			print sys.exc_info()[0], sys.exc_info()[1]
			log.info("Error reading descriptorfile %s" % descriptorfile)
	descriptors.sort(lambda x, y: cmp(x.id, y.id))

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
			remove = FALSE

			for exclude in excludes:
				if exclude in tests[index].groups:
					remove = TRUE
					break

			if remove:
				tests.pop(index)
			else:
				index = index +1
				
	if includes != []:
		index = 0
		while index != len(tests):
			keep = FALSE
				
			for include in includes:
				if include in tests[index].groups:
					keep = TRUE
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
		

