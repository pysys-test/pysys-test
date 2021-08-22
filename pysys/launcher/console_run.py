# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

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

"""
:meta private: Not part of the PySys API. 
"""


from __future__ import print_function
import os.path, stat, getopt, logging, traceback, sys
import json
import shlex
import multiprocessing
import importlib

import pysys
from pysys import log
from pysys import __version__
from pysys.constants import *
from pysys.launcher import createDescriptors
from pysys.utils.fileutils import toLongPathSafe, fromLongPathSafe
from pysys.exceptions import UserError
from pysys.config.project import Project

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
		self.outsubdir = DEFAULT_OUTDIR
		self.modeinclude = []
		self.modeexclude = []
		self.threads = 1
		self.name=name
		self.userOptions = {}
		self.descriptors = []
		self.grep = None
		self.optionString = 'hrpyv:a:t:i:e:c:o:m:n:j:b:X:gG:'
		self.optionList = ["help","record","purge","verbosity=","type=","trace=","include=","exclude=","cycle=","outdir=","mode=","modeinclude=","modeexclude=","threads=", "abort=", 'validateOnly', 'progress', 'printLogs=', 'grep=', 'ci']


	def getProjectHelp(self):
		help = Project.getInstance().projectHelp
		if not help: return None

		lines = help.rstrip().split('\n')
		# delete blank lines at start
		while lines and not lines[0].strip():
			del lines[0]
		if not lines: return None
		
		# strip initial indentation and convert tabs to spaces
		for i in range(len(lines)):
			l = lines[i].replace('\t', ' '*3) # this is the amount of indentation we use for the standard help message
			if i == 0:
				indenttostrip = len(l) - len(l.lstrip())
				indenttoadd = ''
				if l.strip().startswith('-'):
					# align everything with existing content
					indenttoadd = ' '*3
				
			if len(l)-len(l.lstrip()) >= indenttostrip:
				l = indenttoadd+l[indenttostrip:]
			lines[i] = l
		
		# if user hasn't provided their own heading, add ours
		if '----' not in help:
			lines = ['Project help', '-'*12]+lines
		return '\n'.join(lines)

	def printUsage(self, printXOptions):
		"""
		Print the pysys run usage.
		"""
		# printXOptions is not documented so probably little-used
		_PYSYS_SCRIPT_NAME = os.path.basename(sys.argv[0]) if '__main__' not in sys.argv[0] else 'pysys.py'
		print("\nPySys System Test Framework (version %s)" % __version__) 
		print("\nUsage: %s %s [TESTIDS | OPTIONS]*" % (_PYSYS_SCRIPT_NAME, self.name))
		# chars                                                                |80                                      | 120
		print("""
Execution options
-----------------
   -c, --cycle     NUM         run each test the specified number of times
   -o, --outdir    STRING      set the directory to use for each test's output (a relative or absolute path); 
                               setting this is helpful for tagging/naming test output for different invocations 
                               of PySys as you try out various changes to the application under test; tests can 
                               access the final dir name of the outdir using the ${outDirName} project property
   -j, --threads   NUM | xNUM  set the number of jobs (threads) to run tests in parallel (defaults to 1); 
                               specify either an absolute number, or a multiplier on the number of CPUs e.g. "x1.5"; 
                   auto | 0    equivalent to x1.0 (or the PYSYS_DEFAULT_THREADS env var if set)
       --ci                    set optimal options for automated/non-interactive test execution in a CI job: 
                                 --purge --record -j0 --type=auto --mode=ALL --printLogs=FAILURES -XcodeCoverage
   -v, --verbosity LEVEL       set the verbosity for most pysys logging (CRIT, WARN, INFO, DEBUG)
                   CAT=LEVEL   set the verbosity for a specific PySys logging category e.g. -vassertions=, -vprocess=
                               (or to set the verbosity for a non-PySys Python logger category use "python:CAT=LEVEL")
   -y, --validateOnly          test the validate() method without re-running execute()
   -h, --help                  print this message
 
   -Xkey[=value]               set user-defined override attributes to be set on the testcase and runner instances. The 
                               value is available to Python as "self.key". Value is True if not explicitly provided. 
""".rstrip())
		if printXOptions: printXOptions()
		print("""
Advanced:
   -g, --progress              print progress updates after completion of each test
   -r, --record                use configured 'writers' to record the test results (e.g. XML, JUnit, etc)
   -p, --purge                 purge files except run.log from the output directory to save space (unless test fails)
   --printLogs     STRING      indicates for which outcome types the run.log output will be printed to the stdout 
                               console; options are: all|none|failures (default is all).
   -b, --abort     STRING      set the default abort on error property (true|false, overrides 
                               that specified in the project properties)
   -XcodeCoverage              enable collecting and reporting on code coverage with all coverage writers in the project
   -XautoUpdateAssertDiffReferences 
                               this is a special command for automatically updating the reference files when an 
                               assertDiff fails

The PYSYS_DEFAULT_ARGS environment variable can be used to specify any pysys run arguments that you always wish to use, 
for example PYSYS_DEFAULT_ARGS=--progress --outdir __pysys_output. 

Selection and filtering options
-------------------------------
   -i, --include   STRING      set the test groups to include (can be specified multiple times)
   -e, --exclude   STRING      set the test groups to exclude (can be specified multiple times)
   -G, --grep      STRING      run only tests whose title or id contains the specified regex (case insensitive)
   -m, --mode, --modeinclude ALL,PRIMARY,!PRIMARY,MyMode1,!MyMode2,...
                               run tests in the specifies mode(s):
                                 - use PRIMARY to select the test's first/main mode(s) (this is the default)
                                 - use ALL to select all modes
                                 - use !MODE as an alias for modeexclude
                                 - regular expressions can be used
   --modeexclude MyMode1,MyMode2,...
                               run tests excluding specified mode(s); excludes take precedence over includes
   -a, --type      STRING      set the test type to run (auto or manual, default is both)"
   -t, --trace     STRING      set the requirement id for the test run

Test identifiers
----------------
By default, PySys executes all available tests under the current directory will be run. Alternatively to run just a 
subset, one or more tests or sequences of tests can be specified on the command line. In both cases, tests are filtered 
based on the selection options listed above (e.g. --include/--exclude). 

Tests should contain only alphanumeric and the underscore characters. The following syntax is used 
to select an individual test, or a sequence of numbered tests:

   Test_001                   - a single testcase with id equal to or ending with Test_001
   _001                       - a single testcase with id equal to or ending with _001
   1                          - a single testcase ending with number 1 (but not ending '11')
                                (if it has multiple modes, runs the primary mode(s), or uses --mode)
   Test_001~ModeA             - run testcase with id Test_001 in ModeA
   :Test_002                  - all tests up to and including the testcase with id Test_002
   Test_001:                  - all tests from Test_001 onwards
   Test_001:Test_002          - all tests between tests with ids Test_001 and Test_002 (inclusive)
   2 Test_001                 - Test_001 and Test_002
   ^Test.*                    - All tests matching the specified regex

e.g. 
   {scriptname} run -c2 -w4 -u -j=x1.5 Test_007 Test_001: 3:5
   {scriptname} run -vDEBUG --include MYTESTS -Xhost=localhost
""".format(scriptname=_PYSYS_SCRIPT_NAME))
		
		# show project help at the end so it's more prominent
		Project.findAndLoadProject()
		help = self.getProjectHelp()
		if help: print(help)
		
		sys.exit()

	def parseArgs(self, args, printXOptions=None):
		# add any default args first; shlex.split does a great job of providing consistent parsing from str->list, 
		# but need to avoid mangling \'s on windows; since this env var will be different for each OS no need for consistent win+unix behaviour
		if os.getenv('PYSYS_DEFAULT_ARGS',''):
			log.info('Using PYSYS_DEFAULT_ARGS = %s'%os.environ['PYSYS_DEFAULT_ARGS'])
			args = shlex.split(os.environ['PYSYS_DEFAULT_ARGS'].replace(os.sep, os.sep*2 if os.sep=='\\' else os.sep)) + args
		

		printLogsDefault = PrintLogs.ALL
		ci ='--ci' in args
		if ci:
			# to ensure identical behaviour, set these as if on the command line
			# (printLogs we don't set here since we use the printLogsDefault mechanism to allow it to be overridden 
			# by CI writers and/or the command line)
			# Also we don't set --modes=ALL here to allow for it to be overridden explicitly if needed
			args = ['--purge', '--record', '-j0', '--type=auto', '--exclude=manual', '-XcodeCoverage']+args
			printLogsDefault = PrintLogs.FAILURES

		try:
			optlist, self.arguments = getopt.gnu_getopt(args, self.optionString, self.optionList)
		except Exception:
			log.warning("Error parsing command line arguments: %s" % (sys.exc_info()[1]))
			sys.exit(1)

		log.debug('PySys arguments: tests=%s options=%s', self.arguments, optlist)

		EXPR1 = re.compile(r"^[\w\.]*=.*$")
		EXPR2 = re.compile(r"^[\w\.]*$")

		printLogs = None
		defaultAbortOnError = None

		logging.getLogger('pysys').setLevel(logging.INFO)

		# as a special case, set a non-DEBUG log level for the implementation of assertions 
		# so that it doesn't get enabled with -vDEBUG only -vassertions=DEBUG 
		# as it is incredibly verbose and slow and not often useful
		logging.getLogger('pysys.assertions').setLevel(logging.INFO)
				
		for option, value in optlist:
			if option in ("-h", "--help"):
				self.printUsage(printXOptions)	  

			elif option in ['--ci']:
				continue # handled above

			elif option in ("-r", "--record"):
				self.record = True

			elif option in ("-p", "--purge"):
				self.purge = True		  

			elif option in ("-v", "--verbosity"):
				verbosity = value
				if '=' in verbosity:
					loggername, verbosity = value.split('=')
					assert not loggername.startswith('pysys.'), 'The "pysys." prefix is assumed and should not be explicitly specified'
					if loggername.startswith('python:'):
						loggername = loggername[len('python:'):]
						assert not loggername.startswith('pysys'), 'Cannot use python: with pysys.*' # would produce a duplicate log handler
						# in the interests of performance and simplicity we normally only add the pysys.* category 
						logging.getLogger(loggername).addHandler(pysys.internal.initlogging.pysysLogHandler)
					else:
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
					log.warning('Invalid log level "%s"'%verbosity)
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
				
			elif option in ("-a", "--type"):
				self.type = value
				if self.type not in ["auto", "manual"]:
					log.warning("Unsupported test type - valid types are auto and manual")
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
				value = os.path.normpath(value)
				if os.path.isabs(value) and not value.startswith('\\\\?\\'): value = fromLongPathSafe(toLongPathSafe(value))
				self.outsubdir = value
					
			elif option in ("-m", "--mode", "--modeinclude"):
				self.modeinclude = self.modeinclude+[x.strip() for x in value.split(',')]

			elif option in ["--modeexclude"]:
				self.modeexclude = self.modeexclude+[x.strip() for x in value.split(',')]

			elif option in ["-n", "-j", "--threads"]:
				N_CPUS = multiprocessing.cpu_count()
				if value.lower()=='auto': value='0'
				if value.lower().startswith('x'):
					self.threads = max(1, int(float(value[1:])*N_CPUS))
				else:
					self.threads = int(value)
					if self.threads <= 0: self.threads = int(os.getenv('PYSYS_DEFAULT_THREADS', N_CPUS))

			elif option in ("-b", "--abort"):
				defaultAbortOnError = str(value.lower()=='true')
				
			elif option in ["-g", "--progress"]:
				self.progress = True

			elif option in ["--printLogs"]:
				printLogs = getattr(PrintLogs, value.upper(), None)
				if printLogs is None: 
					print("Error parsing command line arguments: Unsupported --printLogs value '%s'"%value)
					sys.exit(1)

			elif option in ["-X"]:
				if '=' in value:
					key, value = value.split('=', 1)
				else:
					key, value = value, 'true'
				
				# best not to risk unintended consequences with matching of other types, but for boolean 
				# it's worth it to resolve the inconsistent behaviour of -Xkey=true and -Xkey that existed until 1.6.0, 
				# and because getting a bool where you expected a string is a bit more likely to give an exception 
				# and be noticed that getting a string where you expected a boolean (e.g. the danger of if "false":)
				if value.lower() == 'true':
					value = True
				elif value.lower() == 'false':
					value = False
				
				self.userOptions[key] = value
			
			elif option in ("-y", "--validateOnly"):
				self.userOptions['validateOnly'] = True

			elif option in ("-G", "--grep"):
				self.grep = value

			else:
				print("Unknown option: %s"%option)
				sys.exit(1)

		if ci and not self.modeinclude: # only set this if there is no explicit --mode arguments
			self.modeinclude = ['ALL']

		# log this once we've got the log levels setup
		log.debug('PySys is installed at: %s; python from %s', os.path.dirname(pysys.__file__), sys.executable)

		# retained for compatibility, but PYSYS_DEFAULT_ARGS is a better way to achieve the same thing
		if os.getenv('PYSYS_PROGRESS','').lower()=='true': self.progress = True
		
		# special hidden dict of extra values to pass to the runner, since we can't change 
		# the public API now
		self.userOptions['__extraRunnerOptions'] = {
			'progressWritersEnabled':self.progress,
			'printLogs': printLogs,
			'printLogsDefault': printLogsDefault, # to use if not provided by a CI writer or cmdline
		}
		
		# load project AFTER we've parsed the arguments, which opens the possibility of using cmd line config in 
		# project properties if needed
		Project.findAndLoadProject(outdir=self.outsubdir)
		
		if defaultAbortOnError is not None: setattr(Project.getInstance(), 'defaultAbortOnError', defaultAbortOnError)
		
		descriptors = createDescriptors(self.arguments, self.type, self.includes, self.excludes, self.trace, self.workingDir, 
			modeincludes=self.modeinclude, modeexcludes=self.modeexclude, expandmodes=True)
		descriptors.sort(key=lambda d: [d.executionOrderHint, d._defaultSortKey])

		# No exception handler above, as any createDescriptors failure is really a fatal problem that should cause us to 
		# terminate with a non-zero exit code; we don't want to run no tests without realizing it and return success

		if self.grep:
			regex = re.compile(self.grep, flags=re.IGNORECASE)
			descriptors = [d for d in descriptors if (regex.search(d.id) or regex.search(d.title))]
		
		return self.record, self.purge, self.cycle, None, self.threads, self.outsubdir, descriptors, self.userOptions

def runTest(args):
	try:
		launcher = ConsoleLaunchHelper(os.getcwd(), "run")
		args = launcher.parseArgs(args)
		
		cls = Project.getInstance().runnerClassname.split('.')
		module = importlib.import_module('.'.join(cls[:-1]))
		runner = getattr(module, cls[-1])(*args)
		runner.start()
	
		for cycledict in runner.results.values():
			for outcome in OUTCOMES:
				if outcome.isFailure() and cycledict.get(outcome, None): sys.exit(2)
		sys.exit(0)
	except Exception as e:
		sys.stderr.write('\nPYSYS FATAL ERROR: %s\n' % e)
		if not isinstance(e, UserError): traceback.print_exc()
		sys.exit(10)
