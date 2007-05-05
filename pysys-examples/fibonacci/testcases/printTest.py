#! /usr/bin/env python2.4
import os, sys
from pysys.launcher.console import ConsolePrintHelper

if __name__ == "__main__":
	printer = ConsolePrintHelper(os.getcwd())
	printer.parseArgs(sys.argv[1:])
	printer.printTests()
