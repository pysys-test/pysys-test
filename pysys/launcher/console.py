# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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
:meta private: Should be no reason for this module to be used outside of the PySys framework itself. 
"""

import os.path, stat, getopt, logging, traceback, sys

import pysys
from pysys import __version__
from pysys.constants import *

from pysys.launcher.console_clean import ConsoleCleanTestHelper, cleanTest
from pysys.launcher.console_print import ConsolePrintHelper, printTest
from pysys.launcher.console_makeproject import makeProject
from pysys.launcher.console_make import *
from pysys.launcher.console_run import ConsoleLaunchHelper, runTest


def printUsage(returncode=0):
	_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
	sys.stdout.write("\nPySys System Test Framework (version %s on Python %s.%s.%s)\n" % (
		__version__, sys.version_info[0], sys.version_info[1], sys.version_info[2]))
	sys.stdout.write("\nUsage: %s [command] [option]* { [tests]* | [testId] }\n" % _PYSYS_SCRIPT_NAME)
	sys.stdout.write("    where [command] can be:\n")
	sys.stdout.write("       makeproject - create the configuration file for a new project of PySys testcases\n")
	sys.stdout.write("       make        - create a new testcase in the current project\n")
	sys.stdout.write("       print | ls  - print a list of tests under the current working directory\n")
	sys.stdout.write("       run         - run a set of tests under the current working directory\n")
	sys.stdout.write("       clean       - clean the output subdirectories of tests under the current working directory\n")
	sys.stdout.write("\n")
	sys.stdout.write("    For more information on the options available to each command, use the -h | --help option, e.g.\n")
	sys.stdout.write("       %s run --help\n" % _PYSYS_SCRIPT_NAME)
	sys.exit(returncode)

def main(args):
	# load project only for options where it's necessary, otherwise we get 
	# warnings about missing project file for first time users
	if len(args) < 1 or args[0] in ['--help', '-h', '--version']: 
		printUsage()
	else:
		import faulthandler
		faulthandler.enable() # writes threads to stderr on fatal errors, and on linux also for signals such as SIGABRT
	
		mode = args[0]
		if mode == "run":
			runTest(args[1:])
		elif mode == "make":
			makeTest(args[1:])
		elif mode == "makeproject":
			makeProject(args[1:])
		elif mode == "print" or mode == 'ls':
			printTest(args[1:])
		elif mode == "clean":
			cleanTest(args[1:])
		elif mode == "debug": # undocumented
			sys.stdout.write(f"Using PySys {__version__} from {os.path.normpath(os.path.dirname(pysys.__file__))}\n")
			sys.stdout.write(f"Using Python {sys.version_info[0]}.{sys.version_info[1]}.{sys.version_info[2]} from {os.path.normpath(sys.executable)}\n")
			sys.stdout.write(f'   with Python libs in {os.path.dirname(stat.__file__)}\n')
			for k in sorted(os.environ.keys()):
				if k.startswith(('PYTHON', 'PYSYS_')): sys.stdout.write(f'   env {k} = "{os.environ[k]}"\n')
			sys.stdout.write('\nProject properties:\n')
			for k,v in Project.findAndLoadProject().properties.items():
				sys.stdout.write(f'   {k} = {v}\n')
		else:
			sys.stderr.write(f'ERROR: Unknown command "{mode}"\n')
			sys.stderr.flush()
			printUsage(returncode=1)
