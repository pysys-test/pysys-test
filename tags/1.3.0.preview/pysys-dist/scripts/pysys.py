#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

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

import os, sys, logging

# the sys.path starts with the directory containing pysys.py which we want to remove as
# that dir might be anywhere and could contain anything; it's not needed for locating 
# the pysys modules since those will be in site-packages once pysys is installed
script_path = os.path.abspath(sys.path[0])
sys.path = [p for p in sys.path if os.path.abspath(p) != script_path]

# before anything else, configure the logger
logging.getLogger().addHandler(logging.NullHandler())
from pysys import log, stdoutHandler
stdoutHandler.setLevel(logging.INFO)
log.addHandler(stdoutHandler)

from pysys.constants import loadproject
loadproject(os.getcwd())

from pysys import __version__
from pysys.constants import *
from pysys.utils.loader import import_module
from pysys.launcher.console import ConsoleLaunchHelper
from pysys.launcher.console import ConsolePrintHelper
from pysys.launcher.console import ConsoleCleanTestHelper

def printUsage():
	sys.stdout.write("\nPySys System Test Framework (version %s)\n" % __version__)
	sys.stdout.write("\nUsage: %s [mode] [option]* { [tests]* | [testId] }\n" % os.path.basename(sys.argv[0]))
	sys.stdout.write("    where [mode] can be;\n")
	sys.stdout.write("       run    - run a set of tests rooted from the current working directory\n")
	sys.stdout.write("       make   - make a new testcase directory structure in the current working directory\n")
	sys.stdout.write("       print  - print details of a set of tests rooted from the current working directory\n")
	sys.stdout.write("       clean  - clean the output subdirectories of tests rooted from the current working directory\n")
	sys.stdout.write("\n")
	sys.stdout.write("    For more information on the options available to each mode, use the -h | --help option, e.g.\n")
	sys.stdout.write("       %s run --help\n" % os.path.basename(sys.argv[0]))
	sys.exit()
	
def runTest(args):
	try:
		launcher = ConsoleLaunchHelper(os.getcwd(), "run")
		args = launcher.parseArgs(args)
		module = import_module(PROJECT.runnerModule, sys.path)
		runner = getattr(module, PROJECT.runnerClassname)(*args)
		runner.start()
	
		for cycledict in runner.results.values():
			for outcome in FAILS:
				if cycledict.get(outcome, None): sys.exit(2)
		sys.exit(0)
	except Exception as e:
		sys.stderr.write('\nWARN: %s\n' % e)
		sys.exit(-1)

def printTest(args):
	try:
		printer = ConsolePrintHelper(os.getcwd(), "print")
		printer.parseArgs(args)
		printer.printTests()
	except Exception as e:
		sys.stderr.write('\nWARN: %s\n\n' % e)

def makeTest(args):
	module = import_module(PROJECT.makerModule, sys.path)
	maker = getattr(module, PROJECT.makerClassname)("make")
	maker.parseArgs(args)
	maker.makeTest()

def cleanTest(args):
	cleaner = ConsoleCleanTestHelper(os.getcwd(), "clean")
	cleaner.parseArgs(args)
	cleaner.clean()


if __name__ == "__main__":
	if len(sys.argv) < 2: 
		printUsage()
	else:
		mode = sys.argv[1]
		if mode == "run":
			runTest(sys.argv[2:])
		elif mode == "make":
			makeTest(sys.argv[2:])
		elif mode == "print":
			printTest(sys.argv[2:])
		elif mode == "clean":
			cleanTest(sys.argv[2:])
		else:
			printUsage()



