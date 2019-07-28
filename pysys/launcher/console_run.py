# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA



from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json

from pysys import log

from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors
from pysys.utils.loader import import_module
from pysys.exceptions import UserError
from pysys.xml.project import Project

class ConsoleLaunchHelper(object):
	def __init__(self, workingDir, name=""):
		self.workingDir = workingDir
		self.arguments = []
		self.record = False
		self.purge = False
		self.type = None
		self.trace = None
		self.progress = False
		self.includes = []
		self.excludes = []
		self.cycle = 1
		self.outsubdir = PLATFORM
		self.modeinclude = []
		self.modeexclude = []
		self.threads = 1
		self.name=name
		self.userOptions = {}
		self.descriptors = []
		self.grep = None
		self.optionString = 'hrpyv:a:t:i:e:c:o:m:n:b:X:gG:'
		self.optionList = ["help","record","purge","verbosity=","type=","trace=","include=","exclude=","cycle=","outdir=","mode=","modeinclude=","modeexclude=","threads=", "abort=", 'validateOnly', 'progress', 'printLogs=', 'grep=']


	def printUsage(self, printXOptions):
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		print("\nPySys System Test Framework (version %s): Console run test helper" % __version__) 
		print("\nUsage: %s %s [option]* [tests]*" % (_PYSYS_SCRIPT_NAME, self.name))
		print("   where [option] includes:")
		print("     -h | --help                  print this message")
		print("     -r | --record                record test results using all configured record writers")
		print("     -p | --purge                 purge the output subdirectory on test pass")
		print("     -v | --verbosity LEVEL       set the verbosity for most pysys logging (CRIT, WARN, INFO, DEBUG)")
		print("                      CAT=LEVEL   set the verbosity for a specific category e.g. assertions=, process=")
		print("     -c | --cycle     INT         set the the number of cycles to run the tests")
		print("     -o | --outdir    STRING      set the name of the directory to use for this run's test output")
		print("     -n | --threads   INT|auto    set the number of worker threads to run the tests (defaults to 1). ")
		print("                                  A value of 'auto' sets to the number of available CPUs, or if set, ")
		print("                                  the value of the PYSYS_DEFAULT_THREADS environment variable.")
		print("     -g | --progress              print progress updates after completion of each test (or set")
		print("                                  the PYSYS_PROGRESS=true environment variable)")
		print("     -b | --abort     STRING      set the default abort on error property (true|false, overrides ")
		print("                                  that specified in the project properties)")
		print("          --printLogs STRING      indicates for which outcome types the run.log output ")
		print("                                  will be printed to the stdout console; ")
		print("                                  options are: all|none|failures, default is all.")
		print("     -y | --validateOnly          test the validate() method without re-running execute()")
		print("     -X               KEY=VALUE   set user defined options to be passed through to the testcase and ")
		print("                                  runner instances. The left hand side string is the data attribute ")
		print("                                  to set, the right hand side string the value (True if not specified) ")
		print("")
		print("    selection/filtering options:")
		print("     -G | --grep      STRING      run only tests whose title or id contains the specified regex")
		print("                                  (matched case insensitively)")
		print("     -m | --mode | --modeinclude  ALL,PRIMARY,!PRIMARY,MyMode1,!MyMode2,...")
		print("                                  run tests in the specifies mode(s):")
		print("                                   - use PRIMARY to select the test's")
		print("                                     first/main mode (this is the default)")
		print("                                   - use ALL to select all modes")
		print("                                   - use !MODE as an alias for modeexclude")
		print("        | --modeexclude           MyMode1,MyMode2,...")
		print("                                  run tests excluding specified mode(s)")
		print("     -a | --type      STRING      set the test type to run (auto or manual, default is both)") 
		print("     -t | --trace     STRING      set the requirement id for the test run")
		print("     -i | --include   STRING      set the test groups to include (can be specified multiple times)")
		print("     -e | --exclude   STRING      set the test groups to exclude (can be specified multiple times)")
		if printXOptions: printXOptions()
		print("")
		print("   and where [tests] describes a set of tests to be run. Note that multiple test sets can be specified, ")
		print("   where none are given all available tests will be run. If an include group is given, only tests that ")
		print("   belong to that group will be run. If an exclude group is given, tests in the group will not be run. ")
		print("   Tests should contain only alphanumeric and the underscore characters. The following syntax is used ")
		print("   to select a test set:")
		print("")
		print("     Test_001                  - a single testcase with id Test_001")
		print("     _001                      - a single testcase ending with _001")
		print("     1                         - a single testcase ending with number 1 (but not ending '11')")
		print("                                 (if it has multiple modes, runs the primary one, or uses --mode)")
		print("     Test_001~ModeA            - run testcase with id Test_001 in ModeA")
		print("     :Test_002                 - up to testcase with id Test_002")
		print("     Test_001:                 - from testcase with id Test_001 onwards")
		print("     Test_001:Test_002         - all tests between tests with ids Test_001 and Test_002")
		print("     2 Test_001                - Test_001 and Test_002")
		print("     ^Test.*                   - All tests matching the specified regex")
		print("")
		print("   e.g. ")
		print("       %s -vDEBUG --include MYTESTS 1:4 Test_007" % _PYSYS_SCRIPT_NAME)
		print("       %s -c2 -Xhost=localhost Test_001:" % _PYSYS_SCRIPT_NAME)
		print("")
		sys.exit()


	def parseArgs(self, args, printXOptions=None):
		try:
			optlist, self.arguments = getopt.gnu_getopt(args, self.optionString, self.optionList)
		except Exception:
			log.warn("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)

		EXPR1 = re.compile("^[\w\.]*=.*$")
		EXPR2 = re.compile("^[\w\.]*$")

		printLogs = None
		
		logging.getLogger('pysys').setLevel(logging.INFO)

		# as a special case, set a non-DEBUG log level for the implementation of assertions 
		# so that it doesn't get enabled with -vDEBUG only -vassertions=DEBUG 
		# as it is incredibly verbose and slow and not often useful
		logging.getLogger('pysys.assertions').setLevel(logging.INFO)
		
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage(printXOptions)	  

			elif option in ("-r", "--record"):
				self.record = True

			elif option in ("-p", "--purge"):
				self.purge = True		  

			elif option in ("-v", "--verbosity"):
				verbosity = value
				if '=' in verbosity:
					loggername, verbosity = value.split('=')
					assert not loggername.startswith('pysys.'), 'The "pysys." prefix is assumed and should not be explicitly specified'
					loggername = 'pysys.'+loggername
				else:
					loggername = None
				
				if verbosity.upper() == "DEBUG":
					verbosity = logging.DEBUG
				elif verbosity.upper() == "INFO":
					verbosity = logging.INFO
				elif verbosity.upper() == "WARN":
					verbosity = logging.WARN
				elif verbosity.upper() == "CRIT":					
					verbosity = logging.CRITICAL
				else:
					log.warn('Invalid log level "%s"'%verbosity)
					sys.exit(1)
				
				if loggername is None:
					# when setting global log level to a higher level like WARN etc we want to affect stdout but 
					# not necessarily downgrade the root level (would make run.log less useful and break 
					# some PrintLogs behaviour)
					stdoutHandler.setLevel(verbosity)
					if verbosity == logging.DEBUG: logging.getLogger('pysys').setLevel(logging.DEBUG)
				else:
					# for specific level setting we need the opposite - only change stdoutHandler if we're 
					# turning up the logging (since otherwise it wouldn't be seen) but also change the specified level
					logging.getLogger(loggername).setLevel(verbosity)
					if verbosity == logging.DEBUG: stdoutHandler.setLevel(logging.DEBUG)
				
			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warn("Unsupported test type - valid types are auto and manual")
					sys.exit(1)

			elif option in ("-t", "--trace"):
				self.trace = value
									
			elif option in ("-i", "--include"):
				self.includes.append(value)

			elif option in ("-e", "--exclude"):
				self.excludes.append(value)			
						
			elif option in ("-c", "--cycle"):
				try:
					self.cycle = int(value)
				except Exception:
					print("Error parsing command line arguments: A valid integer for the number of cycles must be supplied")
					sys.exit(1)

			elif option in ("-o", "--outdir"):
				self.outsubdir = value
					
			elif option in ("-m", "--mode", "--modeinclude"):
				self.modeinclude = self.modeinclude+[x.strip() for x in value.split(',')]

			elif option in ["--modeexclude"]:
				self.modeexclude = self.modeexclude+[x.strip() for x in value.split(',')]

			elif option in ("-n", "--threads"):
				try:
					self.threads = 0 if value.lower()=='auto' else int(value)
				except Exception:
					print("Error parsing command line arguments: A valid integer for the number of threads must be supplied")
					sys.exit(1)

			elif option in ("-b", "--abort"):
				setattr(Project.getInstance(), 'defaultAbortOnError', str(value.lower()=='true'))

			elif option in ["-g", "--progress"]:
				self.progress = True

			elif option in ["--printLogs"]:
				printLogs = getattr(PrintLogs, value.upper(), None)
				if printLogs is None: 
					print("Error parsing command line arguments: Unsupported --printLogs value '%s'"%value)
					sys.exit(1)

			elif option in ["-X"]:
				if EXPR1.search(value) is not None:
				  self.userOptions[value.split('=')[0]] = value.split('=')[1]
				if EXPR2.search(value) is not None:
					self.userOptions[value] = True
			
			elif option in ("-y", "--validateOnly"):
				self.userOptions['validateOnly'] = True

			elif option in ("-G", "--grep"):
				self.grep = value

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)

			
		if os.getenv('PYSYS_PROGRESS','').lower()=='true': self.progress = True
		
		# special hidden dict of extra values to pass to the runner, since we can't change 
		# the public API now
		self.userOptions['__extraRunnerOptions'] = {
			'progressWritersEnabled':self.progress,
			'printLogs': printLogs,
		}
		
		descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace, self.workingDir, 
			modeincludes=self.modeinclude, modeexcludes=self.modeexclude, expandmodes=True)
		descriptors.sort(key=lambda d: [d.executionOrderHint, d._defaultSortKey])

		# No exception handler above, as any createDescriptors failure is really a fatal problem that should cause us to 
		# terminate with a non-zero exit code; we don't want to run no tests without realizing it and return success

		if self.grep:
			regex = re.compile(self.grep, flags=re.IGNORECASE)
			descriptors = [d for d in descriptors if (regex.search(d.id) or regex.search(d.title))]
		
		runnermode = self.modeinclude[0] if len(self.modeinclude)==1 else None # used when supportMultipleModesPerRun=False
		return self.record, self.purge, self.cycle, runnermode, self.threads, self.outsubdir, descriptors, self.userOptions

def runTest(args):
	try:
		launcher = ConsoleLaunchHelper(os.getcwd(), "run")
		args = launcher.parseArgs(args)
		module = import_module(Project.getInstance().runnerModule, sys.path)
		runner = getattr(module, Project.getInstance().runnerClassname)(*args)
		runner.start()
	
		for cycledict in runner.results.values():
			for outcome in FAILS:
				if cycledict.get(outcome, None): sys.exit(2)
		sys.exit(0)
	except Exception as e:
		sys.stderr.write('\nPYSYS FATAL ERROR: %s\n' % e)
		if not isinstance(e, UserError): traceback.print_exc()
		sys.exit(10)
