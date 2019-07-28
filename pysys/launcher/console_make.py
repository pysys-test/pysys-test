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



from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors
from pysys.xml.descriptor import DESCRIPTOR_TEMPLATE
from pysys.xml.project import getProjectConfigTemplates, createProjectConfig, Project
from pysys.basetest import TEST_TEMPLATE
from pysys.utils.loader import import_module
from pysys.exceptions import UserError

class ConsoleMakeTestHelper(object):
	def __init__(self, name=""):
		self.name = name
		self.testId = None
		self.type = "auto"
		self.testdir = os.getcwd()


	def printUsage(self):
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'

		print("\nPySys System Test Framework (version %s): Console make test helper" % __version__) 
		print("\nUsage: %s %s [option]+ [testid]" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -h | --help                 print this message")
		print("       -a | --type     STRING      set the test type (auto or manual, default is auto)")
		print("       -d | --dir      STRING      base path to testcase (default is current working dir)")
		print("")
		print("   and where [testid] is the mandatory test identifier.")
		sys.exit()


	def parseArgs(self, args):
		try:
			optlist, arguments = getopt.gnu_getopt(args, 'ha:d:', ["help","type=","dir="] )
		except Exception:
			print("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
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

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)


		if arguments == []:
			print("A valid string test id must be supplied")
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

def makeTest(args):
	module = import_module(Project.getInstance().makerModule, sys.path)
	maker = getattr(module, Project.getInstance().makerClassname)("make")
	maker.parseArgs(args)
	maker.makeTest()

