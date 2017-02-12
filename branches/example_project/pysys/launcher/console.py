# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net

import sys, os, os.path, stat, glob, getopt, re, string, logging

from pysys import log
from pysys import stdoutHandler

from pysys import __version__
from pysys.constants import *
from pysys.exceptions import *
from pysys.launcher import createDescriptors
from pysys.xml.descriptor import DESCRIPTOR_TEMPLATE
from pysys.basetest import TEST_TEMPLATE

EXPR1 = re.compile("^[\w\.]*=.*$")
EXPR2 = re.compile("^[\w\.]*$")
EXPR3 = re.compile("^[\w]*_([0-9]+)$")


class ConsoleCleanTestHelper:
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.outsubdir = PLATFORM
		self.all = False
		self.name = name
		self.optionString = 'hav:o:'
		self.optionList = ["help","all", "verbosity=","outdir="]


	def printUsage(self, printXOptions):
		print "\nPySys System Test Framework (version %s): Console clean test helper" % __version__ 
		print "\nUsage: %s %s [option]* [tests]*" % (os.path.basename(sys.argv[0]), self.name)
		print "   where [option] includes;"
		print "       -h | --help                 print this message"
		print "       -a | --all                  clean all compiled testclass files"
		print "       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)"
		print "       -o | --outdir    STRING     set the name of the test output subdirectories to clean"
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

			elif option in ("-a", "--all"):
				self.all = True

			elif option in ("-v", "--verbosity"):
				if value.upper() == "DEBUG":
					stdoutHandler.setLevel(logging.DEBUG)
				elif value.upper() == "INFO":
					stdoutHandler.setLevel(logging.INFO)
				elif value.upper() == "WARN":
					stdoutHandler.setLevel(logging.WARN)	
				elif value.upper() == "CRIT":
					stdoutHandler.setLevel(logging.CRITICAL)
				
			elif option in ("-o", "--outdir"):
				self.outsubdir = value


	def clean(self):
		try:
			descriptors = createDescriptors(self.arguments, None, [], [], None, self.workingDir)		
		except Exception, (strerror):
			log.info(strerror)
		else:
			for descriptor in descriptors:
				if self.all:
					if sys.version_info >= (3,):
						cache=os.path.join(os.path.dirname(descriptor.module),"__pycache__")
						if os.path.exists(cache):
							log.info("Deleting pycache: " + cache)
							self.purgeDirectory(cache, True)
					else:
						path = descriptor.module + ".pyc"
						try:
							mode = os.stat(path)[stat.ST_MODE]
							if stat.S_ISLNK(mode):
								os.unlink(path)
							if stat.S_ISREG(mode):
								os.remove(path)
							log.info("Deleting compiled module: " + path)
						except:
							log.debug("Error deleting compiled module: " + path)

				pathToDelete = os.path.join(descriptor.output, self.outsubdir)
				if os.path.exists(pathToDelete):
					log.info("Deleting output directory: " + pathToDelete)
					self.purgeDirectory(pathToDelete, True)
				else:
					log.debug("Output directory does not exist: " + pathToDelete)


	def purgeDirectory(self, dir, delTop=False):
		for file in os.listdir(dir):
			path = os.path.join(dir, file)
			if PLATFORM in ['sunos', 'linux']:
				mode = os.lstat(path)[stat.ST_MODE]
			else:
				mode = os.stat(path)[stat.ST_MODE]
		
			if stat.S_ISLNK(mode):
				os.unlink(path)
			if stat.S_ISREG(mode):
				os.remove(path)
			elif stat.S_ISDIR(mode):
				self.purgeDirectory(path, delTop=True)

		if delTop: os.rmdir(dir)


class ConsolePrintHelper:
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.full = False
		self.groups = False
		self.modes = False
		self.requirements = False
		self.mode = None
		self.type = None
		self.trace = None
		self.includes = []
		self.excludes = []
		self.tests = None
		self.name = name
		self.optionString = 'hfgdrm:a:t:i:e:'
		self.optionList = ["help","full","groups","modes","requirements","mode=","type=","trace=","include=","exclude="] 
		

	def printUsage(self):
		print "\nPySys System Test Framework (version %s): Console print test helper" % __version__ 
		print "\nUsage: %s %s [option]* [tests]*" % (os.path.basename(sys.argv[0]), self.name)
		print "    where options include;"
		print "       -h | --help                 print this message"
		print "       -f | --full                 print full information"
		print "       -g | --groups               print test groups defined"
		print "       -d | --modes                print test modes defined"
		print "       -r | --requirements         print test requirements covered"
		print "       -m | --mode      STRING     print tests that run in user defined mode "
		print "       -a | --type      STRING     print tests of supplied type (auto or manual, default all)"
		print "       -t | --trace     STRING     print tests which cover requirement id " 
		print "       -i | --include   STRING     print tests in included group (can be specified multiple times)"
		print "       -e | --exclude   STRING     do not print tests in excluded group (can be specified multiple times)"
		print ""
		print "   and where [tests] describes a set of tests to be printed to the console. Note that multiple test "
		print "   sets can be specified, and where none are given all available tests will be run. If an include "
		print "   group is given, only tests that belong to that group will be printed. If an exclude group is given, "
		print "   tests in the group will not be run. The following syntax is used to select a test set;"
		print ""
		print "       test1    - a single testcase with id test1"
		print "       :test2   - upto testcase with id test2"
		print "       test1:   - from testcase with id test1 onwards"
		print "       id1:id2  - all tests between tests with ids test1 and test2"
		print ""
		print "   e.g. "
		print "       %s -i group1 -e group2 --full test1:test3" % os.path.basename(sys.argv[0])
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

			elif option in ("-f", "--full"):
				self.full = True
				
			if option in ("-g", "--groups"):
				self.groups = True
				
			if option in ("-d", "--modes"):
				self.modes = True
			
			if option in ("-r", "--requirements"):
				self.requirements = True
				
			elif option in ("-m", "--mode"):
				self.mode = value

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
				
			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)


	def printTests(self):
		try:
			descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace, self.workingDir)		
		except Exception, (strerror):
			log.info(strerror)
		else:
			exit = 0
			if self.groups == True:
				groups = []
				for descriptor in descriptors:
					for group in descriptor.groups:
						if group not in groups:
							groups.append(group)
				print "\nGroups defined: "
				for group in groups:
					print "                 %s" % (group)
				exit = 1

			if self.modes == True:
				modes = []
				for descriptor in descriptors:
					for mode in descriptor.modes:
						if mode not in modes:
							modes.append(mode)
				print "\nModes defined: "
				for mode in modes:
					print "                 %s" % (mode)
				exit = 1

			if self.requirements == True:
				requirements = []
				for descriptor in descriptors:
					for requirement in descriptor.traceability:
						if requirement not in requirements:
							requirements.append(requirement)
				print "\nRequirements covered: "
				for requirement in requirements:
					print "                 %s" % (requirement)
				exit = 1
		
			if exit: return
			
			maxsize = 0
			for descriptor in descriptors:
				if len(descriptor.id) > maxsize: maxsize = len(descriptor.id)
			maxsize = maxsize + 2
			
			for descriptor in descriptors:
				if self.mode and not self.mode in descriptor.modes: continue
				padding = " " * (maxsize - len(descriptor.id))
				if not self.full:
					print "%s:%s%s" % (descriptor.id, padding, descriptor.title)
				else:
					print "=========================================="
					print "		" + descriptor.id
					print "=========================================="
					print descriptor



class ConsoleMakeTestHelper:
	def __init__(self, name=""):
		self.name = name
		self.testId = None
		self.type = "auto"
		self.testdir = os.getcwd()


	def printUsage(self):
		print "\nPySys System Test Framework (version %s): Console make test helper" % __version__ 
		print "\nUsage: %s %s [option]+ [testid]" % (os.path.basename(sys.argv[0]), self.name)
		print "   where [option] includes;"
		print "       -h | --help                 print this message"
		print "       -a | --type     STRING      set the test type (auto or manual, default is auto)"
		print "       -d | --dir      STRING      base path to testcase (default is current working dir)"
		print ""
		print "   and where [testid] is the mandatory test identifier."
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, arguments = getopt.getopt(args, 'ht:d:', ["help","type=","dir="] )
		except:
			print "Error parsing command line arguments: %s" % (sys.exc_info()[1])
			self.printUsage()
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)	

			elif option in ("-d", "--dir"):
				self.testdir = value		

		if arguments == []:
			print "A valid string test id must be supplied"
			self.printUsage()
		else:
			self.testId = arguments[0]

		return self.testId


	def makeTest(self, input=None, output=None, reference=None, descriptor=None, testclass=None, module=None,
				 group="", constantsImport=None, basetestImport=None, basetest=None, teststring=None):
		if input==None: input = DEFAULT_INPUT
		if output==None: output = DEFAULT_OUTPUT
		if reference==None: reference = DEFAULT_REFERENCE
		if descriptor==None: descriptor = DEFAULT_DESCRIPTOR[0]
		if testclass==None: testclass = DEFAULT_TESTCLASS
		if module==None: module = DEFAULT_MODULE
		if constantsImport ==None: constantsImport = "from pysys.constants import *"
		if basetestImport == None: basetestImport = "from pysys.basetest import BaseTest"
		if basetest == None: basetest = "BaseTest"

		log.info("Creating testcase %s ..." % self.testId)
		try:	
			os.makedirs(os.path.join(self.testdir, self.testId))
			log.info("Created directory %s" % os.path.join(self.testdir, self.testId))
		except OSError:
			log.info("Error creating testcase " + os.path.join(self.testdir, self.testId) +  " - directory already exists")
			return
		else:
			os.makedirs(os.path.join(self.testdir, self.testId, input))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, input))
			os.makedirs(os.path.join(self.testdir, self.testId, output))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, output))
			os.makedirs(os.path.join(self.testdir, self.testId, reference))
			log.info("Created directory %s " % os.path.join(self.testdir, self.testId, reference))
			descriptor_fp = open(os.path.join(self.testdir, self.testId, descriptor), "w")
			descriptor_fp.write(DESCRIPTOR_TEMPLATE %(self.type, group, testclass, module))
			descriptor_fp.close()
			log.info("Created descriptor %s " % os.path.join(self.testdir, self.testId, descriptor))
			testclass_fp = open(os.path.join(self.testdir, self.testId, "%s.py" % module), "w")
			if teststring == None:
				testclass_fp.write(TEST_TEMPLATE % (constantsImport, basetestImport, testclass, basetest))
			else:
				testclass_fp.write(teststring)
			testclass_fp.close()
			log.info("Created test class module %s " % os.path.join(self.testdir, self.testId, "%s.py" % module))	
		


class ConsoleLaunchHelper:
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.record = False
		self.purge = False
		self.type = None
		self.trace = None
		self.includes = []
		self.excludes = []
		self.cycle = 1
		self.outsubdir = PLATFORM
		self.mode = None
		self.threads = 1
		self.name=name
		self.userOptions = {}
		self.descriptors = []
		self.optionString = 'hrpyv:a:t:i:e:c:o:m:n:b:X:'
		self.optionList = ["help","record","purge","verbosity=","type=","trace=","include=","exclude=","cycle=","outdir=","mode=","threads=", "abort=", 'validateOnly']


	def printUsage(self, printXOptions):
		print "\nPySys System Test Framework (version %s): Console run test helper" % __version__ 
		print "\nUsage: %s %s [option]* [tests]*" % (os.path.basename(sys.argv[0]), self.name)
		print "   where [option] includes;"
		print "       -h | --help                 print this message"
		print "       -r | --record               record the test results in the working directory"
		print "       -p | --purge                purge the output subdirectory on test pass"
		print "       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)"
		print "       -a | --type      STRING     set the test type to run (auto or manual, default is both)" 
		print "       -t | --trace     STRING     set the requirement id for the test run"
		print "       -i | --include   STRING     set the test groups to include (can be specified multiple times)"
		print "       -e | --exclude   STRING     set the test groups to exclude (can be specified multiple times)"
		print "       -c | --cycle     INT        set the the number of cycles to run the tests"
		print "       -o | --outdir    STRING     set the name of the test output subdirectory"
		print "       -m | --mode      STRING     set the user defined mode to run the tests"
		print "       -n | --threads   INT        set the number of worker threads to run the tests (defaults to 1). "
		print "                                   A value of 0 sets to the number of available CPUs"
		print "       -b | --abort     STRING     set the default abort on error property (true|false, overrides "
		print "                                   that specified in the project properties)"
		print "       -y | --validateOnly         test the validate() method without re-running execute()"
		print "       -X               KEY=VALUE  set user defined options to be passed through to the test and "
		print "                                   runner classes. The left hand side string is the data attribute "
		print "                                   to set, the right hand side string the value (True of not specified) "
		if printXOptions: printXOptions()
		print ""
		print "   and where [tests] describes a set of tests to be run. Note that multiple test sets can be specified, "
		print "   where none are given all available tests will be run. If an include group is given, only tests that "
		print "   belong to that group will be run. If an exclude group is given, tests in the group will not be run. "
		print "   Tests should contain only alphanumeric and the underscore characters. The following syntax is used "
		print "   to select a test set;"
		print ""
		print "       test1                     - a single testcase with id test1"
		print "       :test2                    - up to testcase with id test2"
		print "       test1:                    - from testcase with id test1 onwards"
		print "       test1:test2               - all tests between tests with ids test1 and test2"
		print "       test1 test 2 test5:test9  - test1, test2 and all tests between test5 and test9"
		print "       ^test*                    - all tests matching the regex ^test*"
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
				self.record = True

			elif option in ("-p", "--purge"):
				self.purge = True		  

			elif option in ("-v", "--verbosity"):
				self.verbosity = value
				if self.verbosity.upper() == "DEBUG":
					stdoutHandler.setLevel(logging.DEBUG)
				elif self.verbosity.upper() == "INFO":
					stdoutHandler.setLevel(logging.INFO)
				elif self.verbosity.upper() == "WARN":
					stdoutHandler.setLevel(logging.WARN)
				elif self.verbosity.upper() == "CRIT":					
					stdoutHandler.setLevel(logging.CRITICAL)	

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
									
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

			elif option in ("-n", "--threads"):
				try:
					self.threads = int(value)
				except:
					print "Error parsing command line arguments: A valid integer for the number of threads must be supplied"
					self.printUsage(printXOptions)

			elif option in ("-b", "--abort"):
				setattr(PROJECT, 'defaultAbortOnError', str(value.lower()=='true'))

			elif option in ["-X"]:
				if EXPR1.search(value) is not None:
				  self.userOptions[value.split('=')[0]] = value.split('=')[1]
				if EXPR2.search(value) is not None:
					self.userOptions[value] = True
			
			elif option in ("-y", "--validateOnly"):
				self.userOptions['validateOnly'] = True
		try:
			descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace, self.workingDir)
		except Exception, (strerror):
			log.info(strerror)
			descriptors = []
		return self.record, self.purge, self.cycle, self.mode, self.threads, self.outsubdir, descriptors, self.userOptions
		
