#!/usr/bin/env pyton
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

import sys, os, os.path, getopt, sets, re, string, logging

from pysys import rootLogger
from pysys.constants import *
from pysys.exceptions import *
from pysys.xml.descriptor import XMLDescriptorParser

EXPR1 = re.compile("^[\w\.]*=.*$")
EXPR2 = re.compile("^[\w\.]*$")

consoleLogger = logging.StreamHandler(sys.stdout)
consoleFormatter = logging.Formatter('%(asctime)s %(levelname)-5s %(message)s')
consoleLogger.setFormatter(consoleFormatter)
consoleLogger.setLevel(logging.NOTSET)
rootLogger.addHandler(consoleLogger)

log = logging.getLogger('pysys.launcher.console')
log.setLevel(logging.NOTSET)


def createDescriptors(config, testIdSpecs, includes, excludes):
	if not config:	
		descriptors = []
		descriptorfiles = []
		ignoreSet = sets.Set(OSWALK_IGNORES)
		for root, dirs, files in os.walk(os.getcwd()):
			if DEFAULT_DESCRIPTOR in files: descriptorfiles.append(os.path.join(root, DEFAULT_DESCRIPTOR))
			for ignore in (ignoreSet & sets.Set(dirs)): dirs.remove(ignore)

		for descriptorfile in descriptorfiles:
			try:
				descriptors.append(XMLDescriptorParser(descriptorfile).getContainer())
			except Exception, value:
				print sys.exc_info()[0], sys.exc_info()[1]
				print "Error reading descriptorfile %s" % descriptorfile
		descriptors.sort(lambda x, y: cmp(x.id, y.id))
	else:
		print "Config file launching not yet implemented"
		sys.exit(-1)

	# trim down the list for those tests in the test specifiers 
	tests = []
	index = 0
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
				print sys.exc_info()[1]
				print "Unable to locate requested testcase(s)"
				sys.exit()

	# trim down the list based on the include and exclude suites
	if len(excludes) != 0:
		index = 0
		while index != len(tests):
			remove = FALSE

			for exclude in excludes:
				if exclude in tests[index].suites:
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
				if include in tests[index].suites:
					keep = TRUE
					break

			if not keep:
				tests.pop(index)
			else:
				index = index +1

	if len(tests) == 0:
		print "The supplied options and subset of tests did not result in any tests being selected to run"
		sys.exit()
	else:
		return tests
		


class ConsolePrintHelper:
	def __init__(self):
		self.arguments = []
		self.list = FALSE
		self.full = FALSE
		self.mode = None
		self.includes = []
		self.excludes = []
		self.tests = None
		self.optionString = 'hsfi:e:m:'
		self.optionList = ["help", "suites", "full", "include=", "exclude=", "mode="] 
		

	def printUsage(self):
		print "\nUsage: %s [option]* [tests]*" % os.path.basename(sys.argv[0])
		print "    where options include;"
		print "       -h | --help                 print this message"
		print "       -f | --full                 print full information"
		print "       -s | --suites               print test suites defined"
		print "       -m | --mode      STRING     print tests that run in user defined mode "
		print "       -i | --include   STRING     print tests in included suite (can be specified multiple times)"
		print "       -e | --exclude   STRING     do not print tests in excluded suite (can be specified multiple times)"
		print ""
		print "   and where [tests] describes a set of tests to be printed to the console. Note that multiple test "
		print "   sets can be specified, and where none are given all available tests will be run. If an include "
		print "   suite is given, only tests that belong to that suite will be printed. If an exclude suite is given, "
		print "   tests in the suite will not be run. The following syntax is used to select a test set;"
		print ""
		print "       test1    - a single testcase with id test1"
		print "       :test2   - upto testcase with id test2"
		print "       test1:   - from testcase with id test1 onwards"
		print "       id1:id2  - all tests between tests with ids test1 and test2"
		print ""
		print "   e.g. "
		print "       %s -i suite1 -e suite2 --full test1:test3" % os.path.basename(sys.argv[0])
		print ""
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, self.arguments = getopt.getopt(args, self.optionString, self.optionList)
		except:
			log.warn("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			if option in ("-s", "--suites"):
				self.list = TRUE

			elif option in ("-f", "--full"):
				self.full = TRUE

			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)

			elif option in ("-m", "--mode"):
				self.mode = value


	def printTests(self):
		descriptors = createDescriptors(None, self.arguments, self.includes, self.excludes)		

		if self.list == TRUE:
			suites = []
			for descriptor in descriptors:
				for suite in descriptor.suites:
					if suite not in suites:
						suites.append(suite)
			print "\nCurrent suites: "
			for suite in suites:
				print "                 %s" % (suite)
			print "\n"
			return 

		maxsize = 0
		for descriptor in descriptors:
			if len(descriptor.id) > maxsize: maxsize = len(descriptor.id)
		maxsize = maxsize + 2
		
		for descriptor in descriptors:
			padding = " " * (maxsize - len(descriptor.id))
			if not self.full:
				print "%s:%s%s" % (descriptor.id, padding, descriptor.title)
			else:
				print "=========================================="
				print "		" + descriptor.id
				print "=========================================="
				descriptor.toString()



class ConsoleMakeTestHelper:
	pass



class ConsoleLaunchHelper:
	def __init__(self):
		self.arguments = []
		self.record = FALSE
		self.purge = FALSE
		self.config = None
		self.verbosity = INFO
		self.includes = []
		self.excludes = []
		self.cycle = 1
		self.outsubdir = PLATFORM
		self.mode = None
		self.userOptions = {}
		self.descriptors = []
		self.optionString = 'hrpf:v:i:e:c:o:m:X:'
		self.optionList = ["help","record","purge","config=", "verbosity=", "include=","exclude=","cycle=","outdir=","mode="]


	def printUsage(self, printXOptions):
		print "\nUsage: %s [option]* [tests]*" % os.path.basename(sys.argv[0])
		print "   where the [option] includes;"
		print "       -h | --help                 print this message"
		print "       -r | --record               record the test results in the working directory"
		print "       -p | --purge                purge the output subdirectory on test pass"
		print "       -f | --config    STRING     use specified config file for locating the test descriptors"
		print "       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)"
		print "       -i | --include   STRING     set the test suites to include (can be specified multiple times)"
		print "       -e | --exclude   STRING     set the test suites to exclude (can be specified multiple times)"
		print "       -c | --cycle     INT        set the the number of cycles to run the tests"
		print "       -o | --outdir    STRING     set the name of the test output subdirectory"
		print "       -m | --mode      STRING     set the user defined mode to run the tests"
		print "       -X               KEY=VALUE  set user defined options to be passed through to the test and "
		print "                                   runner classes. The left hand side string is the data attribute "
		print "                                   to set, the right hand side string the value (TRUE of not specified) "
		if printXOptions: printXOptions()
		print ""
		print "   and where [tests] describes a set of tests to be run. Note that multiple test sets can be specified, "
		print "   where none are given all available tests will be run. If an include suite is given, only tests that "
		print "   belong to that suite will be run. If an exclude suite is given, tests in the suite will not be run. "
		print "   The following syntax is used to select a test set;"
		print ""
		print "       test1    - a single testcase with id test1"
		print "       :test2   - upto testcase with id test2"
		print "       test1:   - from testcase with id test1 onwards"
		print "       id1:id2  - all tests between tests with ids test1 and test2"
		print ""
		print "   e.g. "
		print "       %s -vDEBUG --include MYTESTS test1:test4 test7" % os.path.basename(sys.argv[0])
		print "       %s -c2 -Xhost=localhost test1:" % os.path.basename(sys.argv[0])
		print ""
		sys.exit()


	def parseArgs(self, args, printXOptions=None):
		try:
			optlist, self.arguments = getopt.getopt(args, self.optionString, self.optionList)
		except:
			log.warn("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)

		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage(printXOptions)	  

			elif option in ("-r", "--record"):
				self.record = TRUE

			elif option in ("-u", "--purge"):
				self.purge = TRUE		  

			elif option in ("-f", "--config"):
				self.config = value

			elif option in ("-v", "--verbosity"):
				self.verbosity = value
				if self.verbosity == "DEBUG":
					rootLogger.setLevel(logging.DEBUG)
				elif self.verbosity == "INFO":
					rootLogger.setLevel(logging.INFO)
				elif self.verbosity == "WARN":
					rootLogger.setLevel(logging.WARN)	
				elif self.verbosity == "CRIT":
					rootLogger.setLevel(logging.CRITICAL)	

			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)			
						
			elif option in ("-c", "--cycle"):
				try:
					self.cycle = int(value)
				except:
					print "Error parsing command line arguments: A valid integer for the number of cycles must be supplied"
					self.printUsage(printXOptions)

			elif option in ("-o", "--outdir"):
				self.outsubdir = value
					
			elif option in ("-m", "--mode"):
				self.mode = value

			elif option in ("-X"):
				if EXPR1.search(value) != None:
				  exec("self.userOptions['%s'] = '%s'" % (value.split('=')[0], value.split('=')[1]) )
				if EXPR2.search(value) != None:
					exec("self.userOptions['%s'] = %d" % (value, TRUE))


	def runTests(self, runner):
		descriptors = createDescriptors(self.config, self.arguments, self.includes, self.excludes)
		r = runner(self.record, self.purge, self.cycle, self.mode, self.outsubdir, descriptors, self.userOptions)
		r.start()
		r.cleanup()
		



