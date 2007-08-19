#! /usr/bin/env python2.4
import os, sys

# load the project file
from pysys.constants import loadproject
loadproject(os.getcwd())

from pysys.launcher.console import ConsolePrintHelper

if __name__ == "__main__":
	printer = ConsolePrintHelper(os.getcwd())
	printer.parseArgs(sys.argv[1:])
	printer.printTests()
