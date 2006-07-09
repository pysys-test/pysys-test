#! /usr/bin/env python
import os, sys
from pysys.launcher.console import ConsoleMakeTestHelper

if __name__ == "__main__":
	printer = ConsoleMakeTestHelper(os.getcwd(), "from pysys.basetest import BaseTest", "BaseTest")
	printer.parseArgs(sys.argv[1:])