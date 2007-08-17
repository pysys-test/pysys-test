#! /usr/bin/env python
import sys
from pysys.launcher.console import ConsoleLaunchHelper
	
if __name__ == "__main__":
	from pysys.baserunner import BaseRunner
	launcher = ConsoleLaunchHelper()
	launcher.parseArgs(sys.argv[1:], printXOptions)
	launcher.runTests(BaseRunner)
