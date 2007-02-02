__all__ = [ "console" ]

import sys, os, os.path, glob, getopt, sets, re, string, logging

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.descriptor import XMLDescriptorParser

log = logging.getLogger('pysys.launcher')
log.setLevel(logging.NOTSET)


def createDescriptors(testIdSpecs, type, includes, excludes, trace, dir=None):
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
				log.info("Unable to locate requested testcase(s)")
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
		log.info("The supplied options and subset of tests did not result in any tests being selected to run")
		raise Exception("The supplied options and subset of tests did not result in any tests being selected to run")
	else:
		return tests
		

