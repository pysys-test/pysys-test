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
:meta private: Not part of the PySys API. 
"""


from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors, MODE_CHARS
from pysys.exceptions import UserError
from pysys.config.project import Project

class ConsolePrintHelper(object):
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.full = False
		self.groups = False
		self.modes = False # print list of available modes
		self.requirements = False
		self.json = False
		self.modefilter = [] # select based on mode
		self.type = None
		self.trace = None
		self.includes = []
		self.excludes = []
		self.tests = None
		self.name = name
		self.sort = None
		self.grep = None
		self.optionString = 'hfgdrm:a:t:i:e:s:G:'
		self.optionList = ["help","full","groups","modes","requirements","mode=","type=","trace=","include=","exclude=", "json", "sort=", "grep="] 
		

	def printUsage(self):
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'

		#######                                                                                                                       |
		print("\nPySys System Test Framework (version %s): Test list printer" % __version__) 
		print("\nUsage: %s %s [option]* [tests]*" % (_PYSYS_SCRIPT_NAME, self.name))
		print("    where options include:")
		print("       -h | --help                 print this message")
		print("")
		print("    output options:")
		print("       -f | --full                 print full information")
		print("       -g | --groups               print test groups defined")
		print("       -d | --modes                print test modes defined")
		print("       -r | --requirements         print test requirements covered")
		print("       -s | --sort   STRING        sort by: title, id, executionOrderHint")
		print("            --json                 print full information as JSON")
		print("")
		print("    selection/filtering options:")
		print("       -G | --grep      STRING     print only tests whose title or id contains the specified regex")
		print("                                   (matched case insensitively)")
		print("       -m | --mode      STRING     print only tests that run in the specified mode(s)")
		print("                                   (use ! for excludes e.g. -m MyMode1,MyMode2,Other.* or -m !MyMode3)")
		print("       -a | --type      STRING     print only tests of supplied type (auto or manual, default all)")
		print("       -t | --trace     STRING     print only tests which cover requirement id ") 
		print("       -i | --include   STRING     print only tests in included group (can be specified multiple times)")
		print("       -e | --exclude   STRING     do not print tests in excluded group (can be specified multiple times)")
		print("")
		print("   and where [tests] describes a set of tests to be printed to the console. Note that multiple test ")
		print("   sets can be specified, and where none are given all available tests will be run. If an include ")
		print("   group is given, only tests that belong to that group will be printed. If an exclude group is given, ")
		print("   tests in the group will not be run. The following syntax is used to select a test set;")
		print("")
		print("       test1    - a single testcase with id test1")
		print("       :test2   - up to testcase with id test2")
		print("       test1:   - from testcase with id test1 onwards")
		print("       id1:id2  - all tests between tests with ids test1 and test2")
		print("")
		print("   e.g. ")
		print("       %s -i group1 -e group2 --full test1:test3" % _PYSYS_SCRIPT_NAME)
		print("")
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, self.arguments = getopt.gnu_getopt(args, self.optionString, self.optionList)
		except Exception:
			log.warning("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)
			
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage()

			elif option in ("-f", "--full"):
				self.full = True
				
			elif option in ("-g", "--groups"):
				self.groups = True
				
			elif option in ("-d", "--modes"):
				self.modes = True
			
			elif option in ("-r", "--requirements"):
				self.requirements = True
				
			elif option in ("-m", "--mode"):
				self.modefilter = [x.strip() for x in value.split(',')]

			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warning("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
				
			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)

			elif option in ("-s", "--sort"):
				self.sort = value

			elif option in ("-G", "--grep"):
				self.grep = value

			elif option == '--json':
				self.json = True

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)

	def printTests(self):
			Project.findAndLoadProject()
	
			# nb: mode filtering happens later
			descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace, self.workingDir, expandmodes=True if self.modefilter else False, modeincludes=self.modefilter)
			
			if self.grep:
				regex = re.compile(self.grep, flags=re.IGNORECASE)
				descriptors = [d for d in descriptors if (regex.search(d.id) or regex.search(d.title))]
			
			# nb: do this case insensitively since if someone uses inconsistent capitaization they still probably 
			# want related items to show up next to each other
			if not self.sort:
				descriptors.sort(key=lambda d: d._defaultSortKey.lower())
			elif (self.sort.lower()=='id'):
				descriptors.sort(key=lambda d: d.id.lower())
			elif self.sort.lower().replace('-','') in ['executionorderhint', 'orderhint', 'order']:
				descriptors.sort(key=lambda d: [d.executionOrderHint, d._defaultSortKey.lower()])
			elif self.sort.lower()=='title':
				descriptors.sort(key=lambda d: [d.title.lower(), d.title, d._defaultSortKey.lower()])
			else:
				raise UserError('Unknown sort key: %s'%self.sort)
			
			if self.json:
				print(json.dumps([d.toDict() for d in descriptors], indent=3, sort_keys=False))
				return
			
			exit = 0
			if self.groups == True:
				groups = []
				for descriptor in descriptors:
					for group in descriptor.groups:
						if group not in groups:
							groups.append(group)
				print("\nGroups defined: ")
				for group in groups:
					print("  %s" % (group))
				exit = 1

			if self.modes == True:
				modes = []
				for descriptor in descriptors:
					for mode in descriptor.modes:
						if mode not in modes:
							modes.append(mode)
				print("\nModes defined: ")
				for mode in modes:
					print("  %s" % (mode))
				exit = 1

			if self.requirements == True:
				requirements = []
				for descriptor in descriptors:
					for requirement in descriptor.traceability:
						if requirement not in requirements:
							requirements.append(requirement)
				print("\nTraceability requirement ids covered: ")
				for requirement in requirements:
					print("  %s" % (requirement))
				exit = 1
		
			if exit: return
			
			maxsize = 0
			for descriptor in descriptors:
				if len(descriptor.id) > maxsize: maxsize = len(descriptor.id)
			maxsize = maxsize + 2
			
			for descriptor in descriptors:
				padding = " " * (maxsize - len(descriptor.id))
				if not self.full:
					print("%s%s| %s" % (descriptor.id, padding, descriptor.title))
				else:
					print("="*80)
					print(descriptor)

def printTest(args):
	try:
		printer = ConsolePrintHelper(os.getcwd(), "print")
		printer.parseArgs(args)
		printer.printTests()
	except Exception as e:
		sys.stderr.write('\nERROR: %s\n' % e)
		if not isinstance(e, UserError): traceback.print_exc()
		sys.exit(10)
