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
from pysys.exceptions import UserError

class ConsoleCleanTestHelper(object):
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.outsubdir = PLATFORM
		self.all = False
		self.name = name
		self.optionString = 'hav:o:'
		self.optionList = ["help","all", "verbosity=","outdir="]


	def printUsage(self, printXOptions):
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		print("\nPySys System Test Framework (version %s): Console clean test helper" % __version__) 
		print("\nUsage: %s %s [option]* [tests]*" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("       -h | --help                 print this message")
		print("       -a | --all                  clean all compiled testclass files")
		print("       -v | --verbosity STRING     set the verbosity level (CRIT, WARN, INFO, DEBUG)")
		print("       -o | --outdir    STRING     set the name of the test output subdirectories to clean")
		sys.exit()


	def parseArgs(self, args, printXOptions=None):
		try:
			optlist, self.arguments = getopt.getopt(args, self.optionString, self.optionList)
		except Exception:
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
				else:
					log.warn('Invalid log level "%s"'%value)
					sys.exit(1)
				
			elif option in ("-o", "--outdir"):
				self.outsubdir = value

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)


	def clean(self):
			descriptors = createDescriptors(self.arguments, None, [], [], None, self.workingDir)		
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
						except Exception:
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


def cleanTest(args):
	cleaner = ConsoleCleanTestHelper(os.getcwd(), "clean")
	cleaner.parseArgs(args)
	cleaner.clean()

