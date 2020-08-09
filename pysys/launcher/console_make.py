# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

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
Implements ``pysys.py make`` to create new testcases. 
"""

from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors
from pysys.xml.project import Project
from pysys.utils.loader import import_module
from pysys.exceptions import UserError
from pysys.utils.pycompat import openfile, PY2
from pysys.utils.fileutils import toLongPathSafe

class ConsoleMakeTestHelper(object):
	"""
	The default implementation of ``pysys.py make``.
	
	A custom subclass can be specified in the project if required. 
	"""

	TEST_TEMPLATE = '''import pysys
%s
%s

class %s(%s):
	def execute(self):
		pass

	def validate(self):
		pass
	''' # not public API, do not use

	DESCRIPTOR_TEMPLATE ='''<?xml version="1.0" encoding="utf-8"?>
<pysystest type="%s">
  
  <description> 
	<title></title>    
	<purpose><![CDATA[
]]>
	</purpose>
  </description>

  <!-- uncomment this to skip the test:  
  <skipped reason=""/> 
  -->
  
  <classification>
	<groups inherit="true">
	  <group>%s</group>
	</groups>
	<modes inherit="true">
	</modes>
  </classification>

  <data>
	<class name="%s" module="%s"/>
  </data>
  
  <traceability>
	<requirements>
	  <requirement id=""/>     
	</requirements>
  </traceability>
</pysystest>
''' 

	def __init__(self, name=""):
		self.name = name
		self.testId = None
		self.type = "auto"
		self.testdir = os.getcwd()


	def printUsage(self):
		""" Print help info and exit. """
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		#######                                                                                                                        |
		print("\nPySys System Test Framework (version %s): New test maker" % __version__) 
		print("\nUsage: %s %s [option]+ TESTID" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -d | --dir      STRING      parent directory in which to create TESTID (default is current working dir)")
		print("       -a | --type     STRING      set the test type (auto or manual, default is auto)")
		print("       -h | --help                 print this message")
		print("")
		print("   and where TESTID is the id of the new test which should consist of letters, numbers and underscores, ")
		print("   for example: MyApp_perf_001 (numeric style) or InvalidFooBarProducesError ('test that XXX' long string style).")
		sys.exit()


	def parseArgs(self, args):
		""" Parse the command line arguments after ``pysys make``. 
		"""
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
		"""
		Makes a new test on disk. 
		"""
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
			descriptor_fp = openfile(os.path.join(self.testdir, self.testId, descriptor), "w", encoding=None if PY2 else 'utf-8')
			descriptor_fp.write(self.DESCRIPTOR_TEMPLATE %(self.type, group, testclass, module))
			descriptor_fp.close()
			log.info("Created descriptor %s " % os.path.join(self.testdir, self.testId, descriptor))
			testclass_fp = openfile(os.path.join(self.testdir, self.testId, "%s.py" % module), "w")
			if teststring == None:
				testclass_fp.write(self.TEST_TEMPLATE % (constantsImport, basetestImport, testclass, basetest))
			else:
				testclass_fp.write(teststring)
			testclass_fp.close()
			log.info("Created test class module %s " % os.path.join(self.testdir, self.testId, "%s.py" % module))	

def makeTest(args):
	Project.findAndLoadProject()

	cls = Project.getInstance().makerClassname.split('.')
	module = import_module('.'.join(cls[:-1]), sys.path)
	maker = getattr(module, cls[-1])("make")

	maker.parseArgs(args)
	maker.makeTest()

