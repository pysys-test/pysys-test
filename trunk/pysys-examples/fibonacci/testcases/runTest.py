#! /usr/bin/env python2.4
import os, sys, time
from pysys.constants import *
from pysys.baserunner import BaseRunner
from pysys.writer import LogFileResultsWriter
from pysys.launcher.console import ConsoleLaunchHelper

if __name__ == "__main__":
	# create a logfile results writer
	logwriter = LogFileResultsWriter("testsummary_%s.log" % time.strftime('%Y%m%d%H%M%S', time.gmtime(time.time())))

	# create the launcher to parse the command line arguments, and create descriptors
	launcher = ConsoleLaunchHelper(os.getcwd())
	record, purge, cycle, mode, outsubdir, descriptors, userOptions = launcher.parseArgs(sys.argv[1:])
	
	# create the runner and run the tests
	runner = BaseRunner(record, purge, cycle, mode, outsubdir, descriptors, userOptions)
	runner.start(writers=[logwriter])