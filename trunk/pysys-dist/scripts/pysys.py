#!/usr/bin/env python
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

import os, sys, time
script_path = os.path.abspath(sys.path[0])
sys.path = [p for p in sys.path if os.path.abspath(p) != script_path]

from pysys.constants import loadproject
loadproject(os.getcwd())

from pysys import __version__
from pysys.constants import *
from pysys.launcher.console import ConsoleLaunchHelper
from pysys.launcher.console import ConsoleMakeTestHelper
from pysys.launcher.console import ConsolePrintHelper
from pysys.launcher.console import ConsoleCleanTestHelper

def printUsage():
	print "\nPySys System Test Framework (version %s)" % __version__ 
	print "\nUsage: %s [mode] [option]* { [tests]* | [testId] }" % os.path.basename(sys.argv[0])
	print "    where [mode] can be;"
	print "       run    - run a set of tests rooted from the current working directory"
	print "       make   - make a new testcase directory structure in the current working directory"
	print "       print  - print details of a set of tests rooted from the current working directory"
	print "       clean  - clean the output subdirectories of tests rooted from the current working directory"
	print ""
	print "    For more information on the options available to each mode, use the -h | --help option, e.g. "
	print "       %s run --help " % os.path.basename(sys.argv[0])
	sys.exit()
	
def runTest(args):
	launcher = ConsoleLaunchHelper(os.getcwd(), "run")
	record, purge, cycle, mode, outsubdir, descriptors, userOptions = launcher.parseArgs(args)
	exec( "from %s import %s" % (PROJECT.runnerModule, PROJECT.runnerClassname) )
	exec( "runner = %s(record, purge, cycle, mode, outsubdir, descriptors, userOptions)" % (PROJECT.runnerClassname))
	runner.start()

def makeTest(args):
	maker = ConsoleMakeTestHelper(os.getcwd(), "make")
	maker.parseArgs(args)
	maker.makeTest()
	
def printTest(args):
	printer = ConsolePrintHelper(os.getcwd(), "print")
	printer.parseArgs(args)
	printer.printTests()
	
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



