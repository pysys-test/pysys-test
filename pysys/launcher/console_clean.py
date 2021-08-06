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
from pysys.launcher import createDescriptors
from pysys.exceptions import UserError
from pysys.utils.fileutils import deletedir
from pysys.config.project import Project

class ConsoleCleanTestHelper(object):
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.outsubdir = DEFAULT_OUTDIR
		self.all = False
		self.name = name
		self.optionString = 'hav:o:'
		self.optionList = ["help","all", "verbosity=","outdir="]


	def printUsage(self, printXOptions):
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		print("\nPySys System Test Framework (version %s): Test output directory cleaner" % __version__) 
		print("\nUsage: %s %s [option]* [tests]*" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -o | --outdir    STRING     set the name of the test output subdirectories to clean")
		print("       -a | --all                  clean all compiled Python files in addition to test output directory contents")
		print("       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)")
		print("       -h | --help                 print this message")
		sys.exit()


	def parseArgs(self, args, printXOptions=None):
		try:
			optlist, self.arguments = getopt.gnu_getopt(args, self.optionString, self.optionList)
		except Exception:
			log.warning("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)

		from pysys.internal.initlogging import pysysLogHandler, stdoutHandler
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage(printXOptions)	  

			elif option in ("-a", "--all"):
				self.all = True

			elif option in ("-v", "--verbosity"):
				if value.upper() == "DEBUG":
					verbosity = logging.DEBUG
				elif value.upper() == "INFO":
					verbosity = logging.INFO
				elif value.upper() == "WARN":
					verbosity = logging.WARN
				elif value.upper() == "CRIT":					
					verbosity = logging.CRITICAL
				else:
					log.warning('Invalid log level "%s"'%value)
					sys.exit(1)

				log.setLevel(verbosity)
				if verbosity == logging.DEBUG: stdoutHandler.setLevel(verbosity)

				# refresh handler levels
				pysysLogHandler.setLogHandlersForCurrentThread([stdoutHandler])
				
			elif option in ("-o", "--outdir"):
				self.outsubdir = value

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)


	def clean(self):
			Project.findAndLoadProject(outdir=self.outsubdir)

			descriptors = createDescriptors(self.arguments, None, [], [], None, self.workingDir, expandmodes=False)

			for descriptor in descriptors:
				if self.all:
					modulepath = os.path.join(descriptor.testDir, descriptor.module or 'dummy.py')
					cache=os.path.join(os.path.dirname(modulepath),"__pycache__")
					if os.path.isdir(cache):
						log.info("Deleting pycache: " + cache)
						deletedir(cache)
					else:
						log.debug('__pycache__ does not exist: %s', cache)
					path = modulepath + ".pyc"
					if os.path.exists(path):
						log.info("Deleting compiled Python module: " + path)
						os.remove(path)
					else:
						log.debug('.pyc does not exist: %s', path)

				for mode in (descriptor.modes or [None]):
					pathToDelete = os.path.join(descriptor.testDir, descriptor.output, self.outsubdir)

					if os.path.isabs(self.outsubdir): # must delete only the selected testcase
						pathToDelete += "/"+descriptor.id
						
					if mode:
						pathToDelete += '~'+mode

					if os.path.exists(pathToDelete):
						log.info("Deleting output directory: " + pathToDelete)
						deletedir(pathToDelete)
					else:
						log.debug("Output directory does not exist: " + pathToDelete)

def cleanTest(args):
	try:
		cleaner = ConsoleCleanTestHelper(os.getcwd(), "clean")
		cleaner.parseArgs(args)
		cleaner.clean()
	except Exception as e:
		sys.stderr.write('\nERROR: %s\n' % e)
		if not isinstance(e, UserError): traceback.print_exc()
		sys.exit(10)
		
		
