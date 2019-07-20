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

import os.path, stat, getopt, logging, traceback, sys

from pysys import __version__
from pysys.constants import *

"""
@undocumented: main
"""

from pysys.launcher.console_clean import ConsoleCleanTestHelper, cleanTest
from pysys.launcher.console_print import ConsolePrintHelper, printTest
from pysys.launcher.console_makeproject import makeProject
from pysys.launcher.console_make import ConsoleMakeTestHelper, makeTest
from pysys.launcher.console_run import ConsoleLaunchHelper, runTest


def printUsage():
	_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
	sys.stdout.write("\nPySys System Test Framework (version %s on Python %s.%s.%s)\n" % (
		__version__, sys.version_info[0], sys.version_info[1], sys.version_info[2]))
	sys.stdout.write("\nUsage: %s [mode] [option]* { [tests]* | [testId] }\n" % _PYSYS_SCRIPT_NAME)
	sys.stdout.write("    where [mode] can be:\n")
	sys.stdout.write("       makeproject - create the configuration file for a new project of PySys testcases\n")
	sys.stdout.write("       make        - create a new testcase in the current project\n")
	sys.stdout.write("       print       - print list or details of tests under the current working directory\n")
	sys.stdout.write("       run         - run a set of tests under the current working directory\n")
	sys.stdout.write("       clean       - clean the output subdirectories of tests under the current working directory\n")
	sys.stdout.write("\n")
	sys.stdout.write("    For more information on the options available to each mode, use the -h | --help option, e.g.\n")
	sys.stdout.write("       %s run --help\n" % _PYSYS_SCRIPT_NAME)
	sys.exit()

def main(args):
	# load project only for options where it's necessary, otherwise we get 
	# warnings about missing project file for first time users
	if len(args) < 1: 
		printUsage()
	else:
		mode = args[0]
		if mode == "run":
			runTest(args[1:])
		elif mode == "make":
			makeTest(args[1:])
		elif mode == "makeproject":
			makeProject(args[1:])
		elif mode == "print":
			printTest(args[1:])
		elif mode == "clean":
			cleanTest(args[1:])
		else:
			printUsage()
