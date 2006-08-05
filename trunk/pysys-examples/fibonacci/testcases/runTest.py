#! /usr/bin/env python
import sys
from pysys.baserunner import BaseRunner
from pysys.writer import ConsoleResultsWriter
from pysys.launcher.console import ConsoleLaunchHelper

if __name__ == "__main__":
	launcher = ConsoleLaunchHelper()
	launcher.parseArgs(sys.argv[1:])
	launcher.runTests(BaseRunner, [ConsoleResultsWriter])
