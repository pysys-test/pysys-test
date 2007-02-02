#! /usr/bin/env python2.4
import sys
from pysys.baserunner import BaseRunner
from pysys.launcher.console import ConsoleLaunchHelper

if __name__ == "__main__":
	launcher = ConsoleLaunchHelper()
	launcher.parseArgs(sys.argv[1:])
	launcher.runTests(BaseRunner)
