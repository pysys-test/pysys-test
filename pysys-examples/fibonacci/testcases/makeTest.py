#! /usr/bin/env python2.4
import os, sys
from pysys.launcher.console import ConsoleMakeTestHelper

if __name__ == "__main__":
	maker = ConsoleMakeTestHelper(os.getcwd())
	maker.parseArgs(sys.argv[1:])
	maker.makeTest()
