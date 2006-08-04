#! /usr/bin/env python
import sys
from pysys.baserunner import BaseRunner
from pysys.launcher.console import ConsoleLaunchHelper
from pysys.writer.console import ConsoleResultsWriter

	
if __name__ == "__main__":
	launcher = ConsoleLaunchHelper()
	launcher.parseArgs(sys.argv[1:])
	launcher.runTests(BaseRunner, [ConsoleResultsWriter])
