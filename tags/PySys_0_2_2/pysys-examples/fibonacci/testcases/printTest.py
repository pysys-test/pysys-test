#! /usr/bin/env python2.4
import sys
from pysys.launcher.console import ConsolePrintHelper

if __name__ == "__main__":
	printer = ConsolePrintHelper()
	printer.parseArgs(sys.argv[1:])
	printer.printTests()
