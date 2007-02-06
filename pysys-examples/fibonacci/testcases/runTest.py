#! /usr/bin/env python2.4
import sys, time
from pysys.baserunner import BaseRunner
from pysys.writer import LogFileResultsWriter
from pysys.launcher.console import ConsoleLaunchHelper

if __name__ == "__main__":
	# create a logfile results writer
	logwriter = LogFileResultsWriter("testsummary_%s.log" % time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())))

	# parse the args and run the tests
	launcher = ConsoleLaunchHelper()
	launcher.parseArgs(sys.argv[1:])
	launcher.runTests(runner = BaseRunner, writers = [logwriter])
