#!/usr/bin/env python
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


"""
Contains the L{ProcessUser} class used by both L{BaseTest} and L{BaseRunner} 
to provide process-related capabilities including cleanup. 
"""

import time, collections, inspect, locale, fnmatch, sys
import threading
import shutil

from pysys import log, process_lock
from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.filegrep import getmatches
from pysys.utils.logutils import BaseLogFormatter
from pysys.xml.project import Project
from pysys.process.helper import ProcessWrapper
from pysys.utils.allocport import TCPPortOwner
from pysys.utils.fileutils import mkdir, deletedir, pathexists, toLongPathSafe
from pysys.utils.pycompat import *
from pysys.utils.stringutils import compareVersions

STDOUTERR_TUPLE = collections.namedtuple('stdouterr', ['stdout', 'stderr'])


class ProcessUser(object):
	"""Class providing basic operations over interacting with processes.
	
	The ProcessUser class provides the minimum set of operations for managing and interacting with
	processes. The class is designed to be extended by the L{pysys.baserunner.BaseRunner} and 
	L{pysys.basetest.BaseTest} classes so that they prescribe a common set of process operations 
	that any child test can use. Process operations have associated potential outcomes in their
	execution, e.g. C{BLOCKED}, C{TIMEDOUT}, C{DUMPEDCORE} etc. As such the class additionally acts
	as the container for storing the list of outcomes from all child test related actions.
	
	Apart from the C{addOutcome} method this class is not thread-safe, so if 
	you need to access it from multiple threads be sure to add your own locking 
	around use of its fields and methods, including any cleanup functions. 
	
	@ivar input: Location for input to any processes (defaults to current working directory) 
	@type input: string
	@ivar output: Location for output from any processes (defaults to current working directory)
	@type output: string
	
	@ivar disableCoverage: Set to True to disable all code coverage collection for processes 
		started from this instance. For example, to disable coverage in tests tagged with the 
		'performance' group you could use a line like this in your BaseTest::
		
			if 'performance' in self.descriptor.groups: self.disableCoverage = True
		
		The built-in Python code coverage functionality in L{startPython} checks this 
		flag. It is recommended that any other languages supporting code coverage 
		also check the self.disableCoverage flag. 
	
	"""
	
	def __init__(self):
		"""Default constructor.
		
		"""
		self.log = log
		"""The logger instance that should be used to log from this class. """
		
		self.project = Project.getInstance()
		"""The L{pysys.xml.project.Project} instance containing settings for this PySys project."""

		assert self.project or 'doctest' in sys.argv[0], 'Project was not loaded yet' # allow it only during doctest-ing
		
		self.processList = []
		self.processCount = {}
		self.__cleanupFunctions = []

		self.outcome = []
		self.__outcomeReason = ''
		
		self.defaultAbortOnError = self.project.defaultAbortOnError.lower()=='true' if hasattr(self.project, 'defaultAbortOnError') else DEFAULT_ABORT_ON_ERROR
		self.defaultIgnoreExitStatus = self.project.defaultIgnoreExitStatus.lower()=='true' if hasattr(self.project, 'defaultIgnoreExitStatus') else True
		self.__uniqueProcessKeys = {}
		self.__pythonCoverageFile = 0
		
		self.disableCoverage = False
		
		self.lock = threading.RLock()
		"""
		A recursive lock that can be used for protecting the fields of this instance 
		from access by background threads, as needed. 
		"""

	def __getattr__(self, name):
		"""Set self.input or self.output to the current working directory if not defined.
		
		"""
		if name == "input" or name == "output":
			return os.getcwd()
		else:
			raise AttributeError("Unknown class attribute ", name)


	def getInstanceCount(self, displayName):
		"""(Deprecated) Return the number of processes started within the testcase matching the supplied displayName.

		The ProcessUser class maintains a reference count of processes started within the class instance 
		via the L{startProcess()} method. The reference count is maintained against a logical name for 
		the process, which is the C{displayName} used in the method call to L{startProcess()}, or the 
		basename of the command if no displayName was supplied. The method returns the number of 
		processes started with the supplied logical name, or 0 if no processes have been started. 

		@deprecated: The recommended way to allocate unique names is now L{allocateUniqueStdOutErr}
		@param displayName: The process display name
		@return: The number of processes started matching the command basename
		@rtype:  integer
		
		"""
		if displayName in self.processCount:
			return self.processCount[displayName]
		else:
			return 0
		
	
	def allocateUniqueStdOutErr(self, processKey):
		"""Allocate unique filenames of the form `processKey[.n].out/.err` 
		which can be used for the L{startProcess} C{stdouterr} parameter. 
		
		The first time this is called it will return names like 
		`('myprocess.out', 'myprocess.err')`, the second time it will return 
		`('myprocess.1.out', 'myprocess.1.err')`, then 
		`('myprocess.2.out', 'myprocess.2.err')` etc. 
		
		@param processKey: A user-defined identifier that will form the prefix onto which [.n].out is appended
		@return: A STDOUTERR_TUPLE named tuple of (stdout, stderr)
		@rtype:  tuple

		"""
		newval = self.__uniqueProcessKeys.get(processKey, -1)+1
		self.__uniqueProcessKeys[processKey] = newval
		
		suffix = '.%d'%(newval) if newval > 0 else ''
		
		return STDOUTERR_TUPLE(
			os.path.join(self.output, processKey+suffix+'.out'), 
			os.path.join(self.output, processKey+suffix+'.err'), 
			)	

	def getBoolProperty(self, propertyName, default=False):
		"""
		Get a True/False indicating whether the specified property is set 
		on this object (typically as a result of specifying -X on the command 
		line), or else from the project configuration. 
		
		@param propertyName: The name of a property set on the command line 
		or project configuration.
		"""
		val = getattr(self, propertyName, None)
		if val is None: val = getattr(self.project, propertyName, None)
		if val is None: return default
		if val==True or val==False: return val
		return val.lower()=='true'

	def startPython(self, arguments, disableCoverage=False, **kwargs):
		"""
		Start a Python process with the specified arguments. 
		
		Uses the same Python process the tests are running under. 
		
		If PySys was run with the arguments `-X pythonCoverage=true` then 
		`startPython` will add the necessary arguments to enable generation of 
		code coverage. Note that this requried the coverage.py library to be 
		installed. If a project property called `pythonCoverageArgs` exists 
		then its value will be added as (space-delimited) arguments to the 
		coverage tool. 
		
		@param arguments: The arguments to pass to the Python executable. 
		Typically the first one be either the name of a Python script 
		to execute, or '-m' followed by a module name. 
		@param kwargs: See L{startProcess} for detail on available arguments.
		@param disableCoverage: Disables code coverage for this specific 
		process. Coverage can also be disabled by setting 
		`self.disableCoverage==True` on this test instance. 
		@return: The process handle of the process (L{ProcessWrapper}).
		@rtype: L{ProcessWrapper}
		
		"""
		args = arguments
		if 'environs' in kwargs:
			environs = kwargs['environs']
		else:
			environs = kwargs.setdefault('environs', self.getDefaultEnvirons(command=sys.executable))
		if self.getBoolProperty('pythonCoverage') and not disableCoverage and not self.disableCoverage:
			if hasattr(self.project, 'pythonCoverageArgs'):
				args = [a for a in self.project.pythonCoverageArgs.split(' ') if a]+args
			args = ['-m', 'coverage', 'run']+args
			if 'COVERAGE_FILE' not in environs:
				kwargs['environs'] = dict(environs)
				with self.lock:
					self.__pythonCoverageFile += 1
				kwargs['environs']['COVERAGE_FILE'] = self.output+'/.coverage.python.%02d'%(self.__pythonCoverageFile)
		return self.startProcess(sys.executable, arguments=args, **kwargs)

	def startProcess(self, command, arguments, environs=None, workingDir=None, state=FOREGROUND, 
			timeout=TIMEOUTS['WaitForProcess'], stdout=None, stderr=None, displayName=None, 
			abortOnError=None, expectedExitStatus='==0', ignoreExitStatus=None, quiet=False, stdouterr=None):
		"""Start a process running in the foreground or background, and return 
		the L{ProcessWrapper} process object.
		
		Typical use is::
		
			myexecutable = self.startProcess('path_to_my_executable', 
				arguments=['myoperation', 'arg1','arg2'],
				environs=self.createEnvirons(addToLibPath=['my_ld_lib_path']), # if a customized environment is needed
				stdouterr=self.allocateUniqueStdOutErr('myoperation'), # for stdout/err files, pick a suitable logical name for what it's doing
				state=BACKGROUND # or remove for default behaviour of executing in foreground
				)

		The method allows spawning of new processes in a platform independent way. The command, arguments,
		environment and working directory to run the process in can all be specified in the arguments to the
		method, along with the filenames used for capturing the stdout and stderr of the process. Processes may
		be started in the C{FOREGROUND}, in which case the method does not return until the process has completed
		or a time out occurs, or in the C{BACKGROUND} in which case the method returns immediately to the caller
		returning a handle to the process to allow manipulation at a later stage, typically with L{waitProcess}. 
		All processes started in the C{BACKGROUND} and not explicitly killed using the returned process 
		object are automatically killed on completion of the test via the L{cleanup()} destructor.

		@param command: The path to the executable to be launched (should include the full path)
		@param arguments: A list of arguments to pass to the command
		
		@param environs: A dictionary specifying the environment to run the process in. 
			If a None or empty dictionary is passed, L{getDefaultEnvirons} will be invoked to 
			produce a suitable clean default environment for this `command`, containing a minimal set of variables. 
			If you wish to specify a customized environment, L{createEnvirons()} is a great way to create it.
		
		@param workingDir: The working directory for the process to run in (defaults to the testcase output subdirectory)
		
		@param state: Run the process either in the C{FOREGROUND} or C{BACKGROUND} (defaults to C{FOREGROUND})
		
		@param timeout: The timeout period after which to terminate processes running in the C{FOREGROUND}. 
		
		@param stdouterr: The filename prefix to use for the stdout and stderr of the process 
			(`.out`/`.err` will be appended), or a tuple of (stdout,stderr) as returned from 
			L{allocateUniqueStdOutErr}. 
			The stdouterr prefix is also used to form a default display name for 
			the process if none is explicitly provided. 
			The files are created relative to the test output directory. 
			The filenames can be accessed from the returned process object using 
			L{pysys.process.helper.CommonProcessWrapper.stdout} and 
			L{pysys.process.helper.CommonProcessWrapper.stderr}.
		
		@param stdout: The filename used to capture the stdout of the process. It is usually simpler to use `stdouterr` instead of this. 
		@param stderr: The filename used to capture the stderr of the process. It is usually simpler to use `stdouterr` instead of this. 
		
		@param displayName: Logical name of the process used for display 
			(defaults to a string generated from the stdouterr and/or the command).
		
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
			project setting)

		@param expectedExitStatus: The condition string used to determine whether the exit status/code 
			returned by the process is correct. The default is '==0', as an exit code of zero usually indicates success, but if you 
			are expecting a non-zero exit status (for example because you are testing correct handling of 
			a failure condition) this could be set to '!=0' or a specific value such as '==5'. 
	
		@param ignoreExitStatus: If False, a BLOCKED outcome is added if the process terminates with an 
			exit code that doesn't match expectedExitStatus (or if the command cannot be run at all). 
			This can be set to True in cases where you do not care whether the command succeeds or fails, or wish to handle the 
			exit status separately with more complicated logic. 
			
			The default value of ignoreExitStatus=None means the value will 
			be taken from the project property defaultIgnoreExitStatus, which can be configured in the project XML 
			(the recommended default property value is defaultIgnoreExitStatus=False), or is set to True for 
			compatibility with older PySys releases if no project property is set. 
		
		@param quiet: If True, this method will not do any INFO or WARN level logging 
			(only DEBUG level), unless a failure outcome is appended. This parameter can be 
			useful to avoid filling up the log where it is necessary to repeatedly execute a 
			command check for completion of some operation until it succeeds; in such cases 
			you should usually set ignoreExitStatus=True as well since both success and 
			failure exit statuses are valid. 

		@return: The process handle of the process (L{ProcessWrapper}).
		@rtype: L{ProcessWrapper}

		"""
		if ignoreExitStatus == None: ignoreExitStatus = self.defaultIgnoreExitStatus
		workingDir = os.path.join(self.output, workingDir or '')
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		
		if stdouterr:
			if stdout or stderr: raise Exception('Cannot specify both stdouterr and stdout/stderr')
			if isstring(stdouterr):
				stdout = stdouterr+'.out'
				stderr = stdouterr+'.err'
			else:
				stdout, stderr = stdouterr
			if not displayName:
				# Heuristically the name selected by the user for stdout/err usually represents the 
				# logical purpose of the process so makes a great display name. 
				# Also add the command (unless they're the same).
				# NB: We do not do this if stdout/stderr are used since that could break 
				# behaviour for old tests using getInstanceCount.  
				displayName = os.path.basename(stdout.replace('.out',''))
				if os.path.basename(command) not in displayName and displayName not in command:
					displayName = '%s<%s>'%(os.path.basename(command), displayName)
		
		# in case stdout/err were given as non-absolute paths, make sure they go to the output dir not the cwd
		if stdout: stdout = os.path.join(self.output, stdout)
		if stderr: stderr = os.path.join(self.output, stderr)

		if not displayName: displayName = os.path.basename(command)
		
		if not environs: # a truly empty env isn't really usable, so populate it with a minimal default environment instead
			environs = self.getDefaultEnvirons(command=command)
		
		try:
			startTime = time.time()
			process = ProcessWrapper(command, arguments, environs, workingDir, state, timeout, stdout, stderr, displayName=displayName)
			process.start()
			if state == FOREGROUND:
				correctExitStatus = eval('%d %s'%(process.exitStatus, expectedExitStatus))
				
				logmethod = log.info if correctExitStatus else log.warn
				if quiet: logmethod = log.debug
				logmethod("Executed %s, exit status %d%s", displayName, process.exitStatus,
																	", duration %d secs" % (time.time()-startTime) if (int(time.time()-startTime)) > 0 else "")
				
				if not ignoreExitStatus and not correctExitStatus:
					self.addOutcome(BLOCKED, 
						('%s returned non-zero exit code %d'%(process, process.exitStatus))
						if expectedExitStatus=='==0' else
						('%s returned exit code %d (expected %s)'%(process, process.exitStatus, expectedExitStatus)), 
						abortOnError=abortOnError)

			elif state == BACKGROUND:
				(log.info if not quiet else log.debug)("Started %s with process id %d", displayName, process.pid)
		except ProcessError as e:
			if not ignoreExitStatus:
				self.addOutcome(BLOCKED, 'Could not start %s process: %s'%(displayName, e), abortOnError=abortOnError)
			else: # this wouldn't happen during a polling-until-success use case so is always worth logging even in quiet mode
				log.info("%s", sys.exc_info()[1], exc_info=0)
		except ProcessTimeout:
			self.addOutcome(TIMEDOUT, '%s timed out after %d seconds'%(process, timeout), printReason=False, abortOnError=abortOnError)
			(log.warn if not quiet else log.debug)("Process %r timed out after %d seconds, stopping process", process, timeout, extra=BaseLogFormatter.tag(LOG_TIMEOUTS))
			process.stop()
		else:
			with self.lock:
				self.processList.append(process)
				if displayName in self.processCount:
					self.processCount[displayName] = self.processCount[displayName] + 1
				else:
					self.processCount[displayName] = 1
		return process	

	def getDefaultEnvirons(self, command=None, **kwargs):
		"""
		Create a new dictionary of environment variables, suitable for passing to 
		L{startProcess()}, with a minimal clean set of environment variables 
		for this platform, unaffected (as much as possible) by the 
		environment that the tests are being run under. 
		
		This environment contains a minimal PATH/LD_LIBRARY_PATH but does not 
		attempt to replicate the full set of default environment variables 
		on each OS, and in particular it does not include any that identify 
		the the current username or home area. Additional environment 
		variables can be added as needed with L{createEnvirons} overrides. If 
		you don't care about minimizing the risk of your local environment 
		affecting the test processes you start, just use C{environs=os.environ} 
		to allow child processes to inherit the entire parent environment. 
		
		The L{createEnvirons()} and L{startProcess()} methods use this as the 
		basis for creating a new set of default environment variables. 

		If needed this method can be overridden in subclasses to add common 
		environment variables for every process invoked by startProcess, for 
		example to enable options such as code coverage for Java/Python/etc. 
		This is also a good place to customize behaviour for different 
		operating systems. 

		Some features of this method can be configured by setting project 
		properties:
		
		  - `defaultEnvironsDefaultLang`: if set to a value such as `en_US.UTF-8` 
		    the specified value is set for the LANG= variable on Unix; otherwise, 
		    the LANG variable is not set (which might result in use of the 
		    legacy POSIX/C encoding).
		  
		  - `defaultEnvironsTempDir`: if set the expression will be passed to 
		    Python `eval()` and used to set the OS-specific temp directory 
		    environment variables. A typical value is `self.output`.
		
		  - `defaultEnvironsLegacyMode`: set to true to enable compatibility 
		    mode which keeps the behaviour the same as PySys v1.1, 1.2 and 1.3, 
		    namely using a completely empty default environment on Unix, and 
		    a copy of the entire parent environment on Windows. This is not 
		    recommended unless you have a lot of legacy tests that cannot 
		    easily be changed to only set minimal required environment 
		    variables using `createEnvirons()`. 

		@param command: If known, the full path of the executable for which 
			a default environment is being created (when called from `startProcess` 
			this is always set). This allows default environment variables to be 
			customized for different process types e.g. Java, Python, etc. 
			
			When using `command=sys.executable` to launch another copy of the 
			current Python executable, extra items from this process's path 
			environment variables are added to the returned dictionary so that it 
			can start correctly. On Unix-based systems this includes copying all of 
			the load library path environment variable from the parent process. 
		
		@param kwargs: Overrides of this method should pass any additional 
			kwargs down to the super implementation, to allow for future extensions. 
		
		@return: A new dictionary containing the environment variables. 
		"""
		
		assert not kwargs, 'Unknown keyword arguments: %s'%kwargs.keys()

		# this feature is a workaround to maintain compatibility for a bug in PySys v1.1-1.3
		# (see https://github.com/pysys-test/pysys-test/issues/9 for details)
		if getattr(self.project, 'defaultEnvironsLegacyMode','').lower()=='true':
			if IS_WINDOWS: 
				return dict(os.environ)
			else:
				return {}

		e = {}

		# allows setting TEMP to output dir to avoid contamination/filling up of system location
		if getattr(self.project, 'defaultEnvironsTempDir',None)!=None:
			tempDir = eval(self.project.defaultEnvironsTempDir)
			self.mkdir(tempDir)
			if IS_WINDOWS: # pragma: no cover
				e['TEMP'] = e['TMP'] = os.path.normpath(tempDir)
			else:
				e['TMPDIR'] = os.path.normpath(tempDir)
	
		inherited = [] 
		# env vars where it is safe and useful to inherit parent values
		# avoid anything user-specific or that might cause tests to store data 
		# outside the test outpuot directory
		
		if IS_WINDOWS: 
			# for windows there are lots; as a matter of policy we set this to a small 
			# minimal set used by a lot of programs. Keeping up with every single env 
			# var Microsoft sets in every Windows OS release would be too painful, 
			# and better to make users explicitly opt-in to the env vars they want
			inherited.extend(['ComSpec', 'OS', 'PATHEXT', 'SystemRoot', 'SystemDrive', 'windir', 
				'NUMBER_OF_PROCESSORS', 'PROCESSOR_ARCHITECTURE',
				'COMMONPROGRAMFILES', 'COMMONPROGRAMFILES(X86)', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 
				'SYSTEM', 'SYSTEM32'])
		
		for k in inherited:
			if k in os.environ: e[k] = os.environ[k]
		
		# always set PATH/LD_LIB_PATH to clean values from constants.py
		# note that if someone is using an OS with different defaults they won't 
		# be able to edit constants.py but will be able to provide a custom 
		# implementation of this method
		e['PATH'] = PATH
		if LD_LIBRARY_PATH:
			e['LD_LIBRARY_PATH'] = LD_LIBRARY_PATH
		if DYLD_LIBRARY_PATH:
			e['DYLD_LIBRARY_PATH'] = DYLD_LIBRARY_PATH
				
		if not IS_WINDOWS:
			if getattr(self.project, 'defaultEnvironsDefaultLang',''):
				e['LANG'] = self.project.defaultEnvironsDefaultLang
		
		if command == sys.executable:
			# Ensure it's possible to run another instance of this Python, by adding it to the start of the path env vars
			# (but only if full path to the Python executable exactly matches).
			# Keep it as clean as possible by not passing sys.path/PYTHONPATH
			# - but it seems we do need to copy the LD_LIBRARY_PATH from the parent process to ensure the required libraries are present.
			# Do not set PYTHONHOME here, as doesn't work well in virtualenv, and messes up grandchildren 
			# processes that need a different Python version
			e['PATH'] = os.path.dirname(sys.executable)+os.pathsep+e['PATH']

			if LIBRARY_PATH_ENV_VAR != 'PATH': # if it's an os with something like LD_LIBRARY_PATH
				# It's a shame it's necessary to copy parent environment, but there's no sane way to unpick which libraries are 
				# actually required on Unix. Make sure we don't set this env var to an empty string just in case that 
				# doesn't anything weird. 
				newlibpath = (os.getenv(LIBRARY_PATH_ENV_VAR,'')+os.pathsep+e.get(LIBRARY_PATH_ENV_VAR,'')).strip(os.pathsep)
				if newlibpath:
					e[LIBRARY_PATH_ENV_VAR] = newlibpath
				self.log.debug('getDefaultEnvirons was called with a command matching this Python executable; adding required path environment variables from parent environment, including %s=%s', LIBRARY_PATH_ENV_VAR, os.getenv(LIBRARY_PATH_ENV_VAR,''))
			else:  
				self.log.debug('getDefaultEnvirons was called with a command matching this Python executable; adding required path environment variables from parent environment')
		return e

	def createEnvirons(self, overrides=None, addToLibPath=[], addToExePath=[], command=None, **kwargs):
		"""
		Create a new customized dictionary of environment variables suitable 
		for passing to L{startProcess()}'s `environs` argument. 
		
		As a starting point, this method uses the value returned by 
		L{getDefaultEnvirons()} for this `command`. See the documentation on 
		that method for more details. If you don't care about minimizing the 
		risk of your local environment affecting the test processes you start, 
		just use C{environs=os.environ} to allow child processes to inherit the 
		entire parent environment instead of using this method. 
		
		@param overrides: A dictionary of environment variables whose 
		values will be used instead of any existing values. 
		You can use `os.getenv('VARNAME','')` if you need to pass selected 
		variables from the current process as part of the overrides list. 
		If the value is set to None then any variable of this name will be 
		deleted. Use unicode strings if possible (byte strings will be 
		converted depending on the platform). 
		A list of dictionaries can be specified, in which case the latest 
		will override the earlier if there are any conflicts.
		
		@param addToLibPath: A path or list of paths to be prepended to the 
		default value for the environment variable used to load libraries 
		(or the value specified in overrides, if any), 
		i.e. `[DY]LD_LIBRARY_PATH` on Unix or `PATH` on Windows. This is usually 
		more convenient than adding it directly to `overrides`. 

		@param addToExePath: A path or list of paths to be prepended to the 
		default value for the environment variable used to locate executables 
		(or the value specified in overrides, if any), 
		i.e. `PATH` on both Unix and Windows. This is usually 
		more convenient than adding it directly to `overrides`. 
		
		@param command: If known, the full path of the executable for which 
		a default environment is being created (passed to L{getDefaultEnvirons}). 
		
		@param kwargs: Overrides of this method should pass any additional 
		kwargs down to the super implementation, to allow for future extensions. 
		
		@return: A new dictionary containing the environment variables. 
		"""
		
		assert not kwargs, 'Unknown keyword arguments: %s'%kwargs.keys()
		e = self.getDefaultEnvirons(command=command)
		
		if overrides:
			if not isinstance(overrides, list): overrides = [overrides]
			for d in overrides:
				if d:
					for k in d:
						if k.upper() in ['PATH']: k = k.upper() # normalize common ones to avoid chance of duplicates
						if d[k] is None:
							e.pop(k, None) # remove
						else:
							e[k] = d[k]
		
		def preparepath(path):
			if isstring(path): 
				if os.pathsep not in path: path = os.path.normpath(path)
			else:
				path = os.pathsep.join([os.path.normpath(p) for p in path if p])
			return path
			
		if addToLibPath:
			e[LIBRARY_PATH_ENV_VAR] = preparepath(addToLibPath)+os.pathsep+e[LIBRARY_PATH_ENV_VAR]

		if addToExePath:
			e['PATH'] = preparepath(addToExePath)+os.pathsep+e['PATH']
		
		return e

	def stopProcess(self, process, abortOnError=None):
		"""Send a soft or hard kill to a running process to stop its execution.

		This method uses the L{pysys.process.helper} module to stop a running process. Should the request to
		stop the running process fail, a C{BLOCKED} outcome will be added to the outcome list. Failures will
		result in an exception unless the project property defaultAbortOnError=False.

		@param process: The process handle returned from the L{startProcess} method
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
			project setting)

		"""
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		if process.running():
			try:
				process.stop()
				log.info("Stopped process %r", process)
			except ProcessError as e:
				if not abortOnError:
					log.warn("Ignoring failure to stop process %r due to: %s", process, e)
				else:
					self.abort(BLOCKED, 'Unable to stop process %r'%(process), self.__callRecord())


	def signalProcess(self, process, signal, abortOnError=None):
		"""Send a signal to a running process (Unix only).

		This method uses the L{pysys.process.helper} module to send a signal to a running process. Should the
		request to send the signal to the running process fail, a C{BLOCKED} outcome will be added to the
		outcome list.

		@param process: The process handle returned from the L{startProcess} method
		@param signal: The integer value of the signal to send
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
			project setting)

		"""
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		if process.running():
			try:
				process.signal(signal)
				log.info("Sent %d signal to process %r", signal, process)
			except ProcessError as e:
				if not abortOnError:
					log.warn("Ignoring failure to signal process %r due to: %s", process, e)
				else:
					self.abort(BLOCKED, 'Unable to signal process %r'%(process), self.__callRecord())


	def waitProcess(self, process, timeout, abortOnError=None):
		"""Wait for a background process to terminate, return on termination or expiry of the timeout.

		Timeouts will result in an exception unless the project property defaultAbortOnError=False.
		
		This method does not check the exit code, but you can manually 
		check the value of process.exitStatus if you wish to check it succeeded. 

		@param process: The process handle returned from the L{startProcess} method
		@param timeout: The timeout value in seconds to wait before returning
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
		project setting)

		"""
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		assert timeout > 0
		try:
			log.info("Waiting up to %d secs for process %r", timeout, process)
			t = time.time()
			process.wait(timeout)
			if time.time()-t > 10:
				log.info("Process %s terminated after %d secs", process, time.time()-t)
		except ProcessTimeout:
			if not abortOnError:
				log.warn("Ignoring timeout waiting for process %r after %d secs", process, time.time() - t, extra=BaseLogFormatter.tag(LOG_TIMEOUTS))
			else:
				self.abort(TIMEDOUT, 'Timed out waiting for process %s after %d secs'%(process, timeout), self.__callRecord())


	def writeProcess(self, process, data, addNewLine=True):
		"""Write binary data to the stdin of a process.

		This method uses the L{pysys.process.helper} module to write data to the stdin of a process. This
		wrapper around the write method of the process helper only adds checking of the process running status prior
		to the write being performed, and logging to the testcase run log to detail the write.

		@param process: The process handle returned from the L{startProcess()} method
		@param data: The data to write to the process stdin. 
		As only binary data can be written to a process stdin, 
		if a character string rather than a byte object is passed as the data,
		it will be automatically converted to a bytes object using the encoding 
		given by locale.getpreferredencoding(). 
		@param addNewLine: True if a new line character is to be added to the end of the data string

		"""
		if process.running():
			process.write(data, addNewLine)
			log.info("Written to stdin of process %r", process)
			log.debug("  %s" % data)
		else:
			raise Exception("Write to process %r stdin not performed as process is not running", process)


	def waitForSocket(self, port, host='localhost', timeout=TIMEOUTS['WaitForSocket'], abortOnError=None, process=None):
		"""Wait until it is possible to establish a socket connection to a 
		server running on the specified port. 
		
		This method blocks until connection to a particular host:port pair can be established. This is useful for
		test timing where a component under test creates a socket for client server interaction - calling of this
		method ensures that on return of the method call the server process is running and a client is able to
		create connections to it. If a connection cannot be made within the specified timeout interval, the method
		returns to the caller, or aborts the test if abortOnError=True. 
		
		@param port: The port value in the socket host:port pair
		@param host: The host value in the socket host:port pair
		@param timeout: The timeout in seconds to wait for connection to the socket
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
		project setting)
		@param process: If a handle to a process is specified, the wait will abort if 
		the process dies before the socket becomes available.
		"""
		if abortOnError == None: abortOnError = self.defaultAbortOnError

		log.debug("Performing wait for socket creation %s:%s", host, port)

		with process_lock:
			s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			# the following lines are to prevent handles being inherited by 
			# other processes started while this test is runing
			if OSFAMILY =='windows':
				s.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, 0)
				import win32api, win32con
				win32api.SetHandleInformation(s.fileno(), win32con.HANDLE_FLAG_INHERIT, 0)
				s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			else:
				import fcntl
				fcntl.fcntl(s.fileno(), fcntl.F_SETFD, 1)
			
		startTime = time.time()
		while True:
			try:
				s.connect((host, port))
				s.shutdown(socket.SHUT_RDWR)
				
				log.debug("Wait for socket creation completed successfully")
				if time.time()-startTime>10:
					log.info("Wait for socket creation completed after %d secs", time.time()-startTime)
				return True
			except socket.error:
				if process and not process.running():
					msg = "Waiting for socket connection aborted due to unexpected process %s termination"%(process)
					if abortOnError:
						self.abort(BLOCKED, msg, self.__callRecord())
					else:
						log.warn(msg)
					return False

				if timeout:
					currentTime = time.time()
					if currentTime > startTime + timeout:
						msg = "Timed out waiting for creation of socket after %d secs"%(time.time()-startTime)
						if abortOnError:
							self.abort(TIMEDOUT, msg, self.__callRecord())
						else:
							log.warn(msg)
						return False
			time.sleep(0.01)


	def waitForFile(self, file, filedir=None, timeout=TIMEOUTS['WaitForFile'], abortOnError=None):
		"""Wait for a file to exist on disk.
		
		This method blocks until a file is created on disk. This is useful for test timing where 
		a component under test creates a file (e.g. for logging) indicating it has performed all 
		initialisation actions and is ready for the test execution steps. If a file is not created 
		on disk within the specified timeout interval, the method returns to the caller.

		@param file: The basename of the file used to wait to be created
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		@param timeout: The timeout in seconds to wait for the file to be created
		@param abortOnError: If true abort the test on any error outcome (defaults to the defaultAbortOnError
			project setting)

		"""
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
		
		log.debug("Performing wait for file creation: %s", f)
		
		startTime = time.time()
		while True:
			if timeout:
				currentTime = time.time()
				if currentTime > startTime + timeout:

					msg = "Timed out waiting for creation of file %s after %d secs" % (file, time.time()-startTime)
					if abortOnError:
						self.abort(TIMEDOUT, msg, self.__callRecord())
					else:
						log.warn(msg)
					break
					
			time.sleep(0.01)
			if pathexists(f):
				log.debug("Wait for '%s' file creation completed successfully", file)
				return

			
	def waitForSignal(self, file, filedir=None, expr="", condition=">=1", timeout=TIMEOUTS['WaitForSignal'], poll=0.25, 
			ignores=[], process=None, errorExpr=[], abortOnError=None, encoding=None):
		"""Wait for a particular regular expression to be seen on a set number of lines in a text file.
		
		This method blocks until a particular regular expression is seen in a text file on a set
		number of lines. The number of lines which should match the regular expression is given by 
		the C{condition} argument in textual form i.e. for a match on more than 2 lines use condition =\">2\".
		If the regular expression is not seen in the file matching the supplied condition within the 
		specified timeout interval, the method returns to the caller.
		
		Example::
		
			self.waitForSignal('myprocess.log', expr='INFO .*Started successfully', process=myprocess, 
				errorExpr=[' ERROR ', ' FATAL '], encoding='utf-8')

		@param file: The absolute or relative name of the file used to wait for the signal
		
		@param filedir: The dirname of the file (defaults to the testcase output subdirectory)
		
		@param expr: The regular expression to search for in the text file
		
		@param condition: The condition to be met for the number of lines matching the regular expression
		
		@param timeout: The timeout in seconds to wait for the regular expression and to check against the condition
		
		@param poll: The time in seconds to poll the file looking for the regular expression and to check against the condition
		
		@param ignores: A list of regular expressions used to denote lines in the files which should be ignored 
		when matching both `expr` and `errorExpr`. 
		
		@param process: If a handle to the process object producing output is specified, the wait will abort if 
		the process dies before the expected signal appears.
		
		@param errorExpr: Optional list of regular expressions, which if found in the file will cause waiting 
		for the main expression to be aborted with an error outcome. This is useful to avoid waiting a long time for 
		the expected expression when an ERROR is logged that means it will never happen, and also provides 
		much clearer test failure messages in this case. 
		
		@param abortOnError: If true abort the test on any error outcome (defaults to the  defaultAbortOnError
		project setting)
		
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 
		"""
		assert expr, 'expr= argument must be specified when calling waitForSignal'
		
		if abortOnError == None: abortOnError = self.defaultAbortOnError
		if filedir is None: filedir = self.output
		f = os.path.join(filedir, file)
		
		log.debug("Performing wait for signal '%s' %s in file %s with ignores %s", expr, condition, f, ignores)
		
		if errorExpr: assert not isstring(errorExpr), 'errorExpr must be a list of strings not a string'
		
		matches = []
		startTime = time.time()
		msg = "Wait for signal \"%s\" %s in %s" % (expr, condition, os.path.basename(file))
		while 1:
			if pathexists(f):
				matches = getmatches(f, expr, encoding=encoding or self.getDefaultFileEncoding(f), ignores=ignores)
				if eval("%d %s" % (len(matches), condition)):
					if self.project.verboseWaitForSignal.lower()=='true' if hasattr(self.project, 'verboseWaitForSignal') else False:
						log.info("%s completed successfully", msg)
					else:
						log.info("Wait for signal in %s completed successfully", file)
					break
				
				if errorExpr:
					for err in errorExpr:
						errmatches = getmatches(f, err+'.*', encoding=encoding or self.getDefaultFileEncoding(f), ignores=ignores) # add .* to capture entire err msg for a better outcome reason
						if errmatches:
							err = errmatches[0].group(0).strip()
							msg = '%s found during %s'%(quotestring(err), msg)
							# always report outcome for this case; additionally abort if requested to
							self.addOutcome(BLOCKED, outcomeReason=msg, abortOnError=abortOnError, callRecord=self.__callRecord())
							return matches
				
			currentTime = time.time()
			if currentTime > startTime + timeout:
				msg = "%s timed out after %d secs, %s"%(msg, timeout, 
					("with %d matches"%len(matches)) if pathexists(f) else 'file does not exist')
				
				if abortOnError:
					self.abort(TIMEDOUT, msg, self.__callRecord())
				else:
					log.warn(msg, extra=BaseLogFormatter.tag(LOG_TIMEOUTS))
				break
			
			if process and not process.running():
				msg = "%s aborted due to process %s termination"%(msg, process)
				if abortOnError:
					self.abort(BLOCKED, msg, self.__callRecord())
				else:
					log.warn(msg)
				break

			time.sleep(poll)
		return matches


	def addCleanupFunction(self, fn):
		""" Registers a zero-arg function that will be called as part of the cleanup of this object.
		
		Cleanup functions are invoked in reverse order with the most recently added first (LIFO), and
		before the automatic termination of any remaining processes associated with this object.
		
		e.g. self.addCleanupFunction(lambda: self.cleanlyShutdownProcessX(params))
		
		"""
		with self.lock:
			if fn and fn not in self.__cleanupFunctions: 
				self.__cleanupFunctions.append(fn)


	def cleanup(self):
		""" Cleanup function that frees resources managed by this object. 

		Should be called exactly once when this object is no longer needed. Instead of overriding
		this function, use L{addCleanupFunction}.
		
		"""
		try:
			# although we don't yet state this method is thread-safe, make it 
			# as thread-safe as possible by using swap operations
			with self.lock:
				cleanupfunctions, self.__cleanupFunctions = self.__cleanupFunctions, []
			if cleanupfunctions:
				log.info('')
				log.info('cleanup:')
			for fn in reversed(cleanupfunctions):
				try:
					log.debug('Running registered cleanup function: %r'%fn)
					fn()
				except Exception as e:
					log.exception('Error while running cleanup function: ')
		finally:
			with self.lock:
				processes, self.processList = self.processList, []
			for process in processes:
				try:
					if process.running(): process.stop()
				except Exception:
					log.info("caught %s: %s", sys.exc_info()[0], sys.exc_info()[1], exc_info=1)
			self.processCount = {}
			
			log.debug('ProcessUser cleanup function done.')
		

	def addOutcome(self, outcome, outcomeReason='', printReason=True, abortOnError=False, callRecord=None, override=False):
		"""Add a validation outcome (and optionally a reason string) to the validation list.
		
		The method provides the ability to add a validation outcome to the internal data structure 
		storing the list of validation outcomes. Multiple validations may be performed, the current
		supported validation outcomes of which are:
				
		  - L{pysys.constants.SKIPPED}
		  - L{pysys.constants.DUMPEDCORE}
		  - L{pysys.constants.TIMEDOUT}
		  - L{pysys.constants.FAILED}
		  - L{pysys.constants.NOTVERIFIED}
		  - L{pysys.constants.INSPECT}
		  - L{pysys.constants.PASSED}
		
		The outcomes are considered to have a precedence order, as defined by the order of the outcomes listed
		above. Thus a C{BLOCKED} outcome has a higher precedence than a C{PASSED} outcome. The outcomes are defined 
		in L{pysys.constants}. 
		
		This method is thread-safe. 
		
		@param outcome: The outcome to add
		
		@param outcomeReason: A string summarizing the reason for the outcome, 
		for example "Grep on x.log contains 'ERROR: server failed'". 
		
		@param printReason: If True the specified outcomeReason will be printed
		
		@param abortOnError: If true abort the test on any error outcome. This should usually be set to 
		False for assertions, or the configured `self.defaultAbortOnError` setting (typically True) for 
		operations that involve waiting. 
		
		@param callRecord: An array of strings indicating the call stack that lead to this outcome. This will be appended
		to the log output for better test triage.
		
		@param override: Remove any existing test outcomes when adding this one, ensuring 
		that this outcome is the one and only one reported even if an existing outcome 
		has higher precedence. 
		"""
		assert outcome in PRECEDENT, outcome # ensure outcome type is known, and that numeric not string constant was specified! 
		with self.lock:
			if abortOnError == None: abortOnError = self.defaultAbortOnError
			if outcomeReason is None:
				outcomeReason = ''
			else: 
				if PY2 and isinstance(outcomeReason, str): 
					# The python2 logger is very unhappy about byte str objects containing 
					# non-ascii characters (specifically it will fail to log them and dump a 
					# traceback on stderr). Since it's pretty important that assertion 
					# messages and test outcome reasons don't get swallowed, add a 
					# workaround for this here. Not a problem in python 3. 
					outcomeReason = outcomeReason.decode('ascii', errors='replace')
				outcomeReason = outcomeReason.strip().replace(u'\t', u' ')
			
			if override: 
				log.debug('addOutcome is removing existing outcome(s): %s with reason "%s"', [LOOKUP[o] for o in self.outcome], self.__outcomeReason)
				del self.outcome[:]
				self.__outcomeReason = None
			old = self.getOutcome()
			if (old == NOTVERIFIED and not self.__outcomeReason): old = None
			self.outcome.append(outcome)

			#store the reason of the highest precedent outcome
			
			# although we should print whatever is passed in, store a version with control characters stripped 
			# out so that it's easier to read (e.g. coloring codes from third party tools)
			if self.getOutcome() != old: self.__outcomeReason = re.sub(u'[\x00-\x08\x0b\x0c\x0e-\x1F]', '', outcomeReason)
			if outcome in FAILS and abortOnError:
				if callRecord==None: callRecord = self.__callRecord()
				self.abort(outcome, outcomeReason, callRecord)

			if outcomeReason and printReason:
				if outcome in FAILS:
					if callRecord==None: callRecord = self.__callRecord()
					log.warn(u'%s ... %s %s', outcomeReason, LOOKUP[outcome].lower(), u'[%s]'%','.join(callRecord) if callRecord!=None else u'',
							 extra=BaseLogFormatter.tag(LOOKUP[outcome].lower(),1))
				else:
					log.info(u'%s ... %s', outcomeReason, LOOKUP[outcome].lower(), extra=BaseLogFormatter.tag(LOOKUP[outcome].lower(),1))

	def abort(self, outcome, outcomeReason, callRecord=None):
		"""Raise an AbortException.
		
		See also L{skipTest}. 

		@param outcome: The outcome, which will override any existing outcomes previously recorded.
		@param outcomeReason: A string summarizing the reason for the outcome
		
		"""
		raise AbortExecution(outcome, outcomeReason, callRecord)


	def skipTest(self, outcomeReason, callRecord=None):
		"""Raise an AbortException that will set the test outcome to SKIPPED and 
		ensure that the rest of the execute() and validate() methods do not execute. 
		
		This is useful when a test should not be executed in the current mode or platform. 

		@param outcomeReason: A string summarizing the reason the test is being skipped, for example
		"Feature X is not supported on Windows". 
		"""
		raise AbortExecution(SKIPPED, outcomeReason, callRecord)

	def getOutcome(self):
		"""Get the overall outcome based on the precedence order.
				
		The method returns the overall outcome of the test based on the outcomes stored in the internal data
		structure. The precedence order of the possible outcomes is used to determined the overall outcome 
		of the test, e.g. if C{PASSED}, C{BLOCKED} and C{FAILED} were recorded during the execution of the test, 
		the overall outcome would be C{BLOCKED}. 
		
		The method returns the integer value of the outcome as defined in L{pysys.constants}. To convert this 
		to a string representation use the L{pysys.constants.LOOKUP} dictionary i.e. C{LOOKUP[test.getOutcome()]}.
		
		@return: The overall outcome
		@rtype:  integer

		"""	
		with self.lock:
			if len(self.outcome) == 0: return NOTVERIFIED
			return sorted(self.outcome, key=lambda x: PRECEDENT.index(x))[0]


	def getOutcomeReason(self):
		"""Get the reason string for the current overall outcome (if specified).
				
		@return: The overall test outcome reason or '' if not specified
		@rtype:  string

		"""	
		with self.lock:
			fails = len([o for o in self.outcome if o in FAILS])
			if self.__outcomeReason and (fails > 1): return u'%s (+%d other failures)'%(self.__outcomeReason, fails-1)
			return self.__outcomeReason


	def getNextAvailableTCPPort(self):
		"""Allocate a TCP port.

		"""
		o = TCPPortOwner()
		self.addCleanupFunction(lambda: o.cleanup())
		return o.port


	def __callRecord(self):
		"""Retrieve a call record outside of this module, up to the execute or validate method of the test case.

		"""
		stack=[]
		from pysys.basetest import BaseTest
		if isinstance(self, BaseTest):
			for record in inspect.stack():
				info = inspect.getframeinfo(record[0])
				if (self.__skipFrame(info.filename, ProcessUser) ): continue
				if (self.__skipFrame(info.filename, BaseTest) ): continue
				stack.append( '%s:%s' % (os.path.basename(info.filename).strip(), info.lineno) )
				if (os.path.splitext(info.filename)[0] == os.path.splitext(os.path.join(self.descriptor.testDir, self.descriptor.module))[0] and (info.function == 'execute' or info.function == 'validate')): return stack
		return None


	def __skipFrame(self, file, clazz):
		"""Private method to check if a file is that for a particular class.

		@param file: The filepatch to check
		@param clazz: The class to check against

		"""
		return os.path.splitext(file)[0] == os.path.splitext(sys.modules[clazz.__module__].__file__)[0]


	def getExprFromFile(self, path, expr, groups=[1], returnAll=False, returnNoneIfMissing=False, encoding=None):
		""" Searches for a regular expression in the specified file, and returns it. 

		If the regex contains groups, the specified group is returned. If the expression is not found, an exception is raised,
		unless getAll=True or returnNoneIfMissing=True. For example;

		self.getExprFromFile('test.txt', 'myKey="(.*)"') on a file containing 'myKey="foobar"' would return "foobar"
		self.getExprFromFile('test.txt', 'foo') on a file containing 'myKey=foobar' would return "foo"
		
		@param path: file to search (located in the output dir unless an absolute path is specified)
		@param expr: the regular expression, optionally containing the regex group operator (...)
		@param groups: which regex groups (as indicated by brackets in the regex) shoud be returned; default is ['1'] meaning 
		the first group. If more than one group is specified, the result will be a tuple of group values, otherwise the
		result will be the value of the group at the specified index.
		@param returnAll: returns all matching lines if True, the first matching line otherwise.
		@param returnNoneIfMissing: set this to return None instead of throwing an exception
		if the regex is not found in the file
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 
		"""
		with openfile(os.path.join(self.output, path), 'r', encoding=encoding or self.getDefaultFileEncoding(os.path.join(self.output, path))) as f:
			matches = []
			for l in f:
				match = re.search(expr, l)
				if not match: continue
				if match.groups():
					if returnAll: 
						matches.append(match.group(*groups))
					else: 
						return match.group(*groups) 
				else:
					if returnAll: 
						matches.append(match.group(0))
					else: 
						return match.group(0)

			if returnAll: return matches
			if returnNoneIfMissing: return None
			raise Exception('Could not find expression %s in %s'%(quotestring(expr), os.path.basename(path)))


	def logFileContents(self, path, includes=None, excludes=None, maxLines=20, tail=False, encoding=None):
		""" Logs some or all of the lines in the specified file.
		
		If the file does not exist or cannot be opened, does nothing. The method is useful for providing key
		diagnostic information (e.g. error messages from tools executed by the test) directly in run.log, or
		to make test failures easier to triage quickly. 
		
		@param path: May be an absolute, or relative to the test output directory
		@param includes: Optional list of regex strings. If specified, only matches of these regexes will be logged
		@param excludes: Optional list of regex strings. If specified, no line containing these will be logged
		@param maxLines: Upper limit on the number of lines from the file that will be logged. Set to zero for unlimited
		@param tail: Prints the _last_ 'maxLines' in the file rather than the first 'maxLines'
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 
		
		@return: True if anything was logged, False if not
		
		"""
		if not path: return False
		actualpath= os.path.join(self.output, path)
		try:
			# always open with a specific encoding not in bytes mode, since otherwise we can't reliably pass the read lines to the logger
			f = openfile(actualpath, 'r', encoding=encoding or self.getDefaultFileEncoding(actualpath) or locale.getpreferredencoding(), errors='replace')
		except Exception as e:
			self.log.debug('logFileContents cannot open file "%s": %s', actualpath, e)
			return False
		try:
			lineno = 0
			def matchesany(s, regexes):
				assert not isstring(regexes), 'must be a list of strings not a string'
				for x in regexes:
					m = re.search(x, s)
					if m: return m.group(0)
				return None
			
			tolog = []
			
			for l in f:
				l = l.rstrip()
				if not l: continue
				if includes:
					l = matchesany(l, includes)
					if not l: continue
				if excludes and matchesany(l, excludes): continue
				lineno +=1
				tolog.append(l)
				if maxLines:
					if not tail and len(tolog) == maxLines:
						tolog.append('...')
						break
					if tail and len(tolog)==maxLines+1:
						del tolog[0]
		finally:
			f.close()
			
		if not tolog:
			return False
			
		logextra = BaseLogFormatter.tag(LOG_FILE_CONTENTS)
		self.log.info(u'Contents of %s%s: ', os.path.normpath(path), ' (filtered)' if includes or excludes else '', extra=logextra)
		for l in tolog:
			self.log.info(u'  %s'%(l), extra=logextra)
		self.log.info('  -----', extra=logextra)
		self.log.info('', extra=logextra)
		return True

	def mkdir(self, path):
		"""
		Create a directory, with recursive creation of any parent directories.
		
		This function is a no-op (does not throw) if the directory already exists. 
		
		@param path: The path to be created. This can be an absolute path or 
		relative to the testcase output directory.
		
		@return: the absolute path of the new directory, to facilitate fluent-style method calling. 
		"""
		path = os.path.join(self.output, path)
		mkdir(path)
		return path

	def deletedir(self, path, **kwargs): return self.deleteDir(path, **kwargs)

	def deleteDir(self, path, **kwargs):
		"""
		Recursively delete the specified directory. 
		
		Does nothing if it does not exist. Raises an exception if the deletion fails. 
		
		@param path: The path to be deleted. This can be an absolute path or 
		relative to the testcase output directory.
		
		@param kwargs: Any additional arguments are passed to 
		L{pysys.utils.fileutils.deletedir()}. 
		"""
		deletedir(os.path.join(self.output, path), **kwargs)
		
	def getDefaultFileEncoding(self, file, **xargs):
		"""
		Specifies what encoding should be used to read or write the specified 
		text file.
		
		This method is used to select the appropriate encoding whenever PySys 
		needs to open a file, for example to wait for a signal, for a 
		file-based assertion, or to write a file with replacements. 
		Many methods allow the encoding to be overridden for just that call, 
		but getDefaultFileEncoding exists to allow global defaults to be specified 
		based on the filename. 
		
		For example, this method could be overridden to specify that utf-8 encoding 
		is to be used for opening filenames ending in .xml, .json and .yaml. 
		
		The default implementation of this method uses pysysproject.xml 
		configuration rules such as::
		
			<default-file-encoding pattern="*.xml" encoding="utf-8"/>
		
		A return value of None indicates default behaviour, which on Python 3 is to 
		use the default encoding, as specified by python's 
		locale.getpreferredencoding(), and on Python 2 is to use binary "str" 
		objects with no character encoding or decoding applied. 
		
		@param file: The filename to be read or written. This may be an 
		absolute path or a relative path.
		 
		@param xargs: Ensure that an **xargs argument is specified so that 
		additional information can be passed to this method in future releases. 
		
		@return: The encoding to use for this file, or None if default behaviour is 
		to be used.
		"""
		file = file.replace('\\','/').lower() # normalize slashes and ignore case
		for e in self.project.defaultFileEncodings:
			# first match wins
			if fnmatch.fnmatchcase(file, e['pattern'].lower()) or fnmatch.fnmatchcase(os.path.basename(file), e['pattern'].lower()):
				return e['encoding']
		return None
	
	@staticmethod
	def compareVersions(v1, v2):
		""" Compares two alphanumeric dotted version strings to see which is more recent. 
		
		Example usage::
		
			if self.compareVersions(thisversion, '1.2.alpha-3') > 0:
				... # thisversion is newer than 1.2.alpha-3 

		The comparison algorithm ignores case, and normalizes separators ./-/_ 
		so that `'1.alpha2'=='1Alpha2'`. Any string components are compared 
		lexicographically with other strings, and compared to numbers 
		strings are always considered greater. 

		>>> ProcessUser.compareVersions('10-alpha5.dev10', '10alpha-5-dEv_10') == 0 # normalization of case and separators
		True

		>>> ProcessUser.compareVersions(b'1....alpha.2', u'1Alpha2') == 0 # ascii byte and unicode strings both supported
		True

		>>> ProcessUser.compareVersions('1.2.0', '1.2')
		0

		>>> ProcessUser.compareVersions('1.02', '1.2')
		0

		>>> ProcessUser().compareVersions('1.2.3', '1.2') > 0
		True

		>>> ProcessUser.compareVersions('1.2', '1.2.3')
		-1
		
		>>> ProcessUser.compareVersions('10.2', '1.2')
		1

		>>> ProcessUser.compareVersions('1.2.text', '1.2.0') # letters are > numbers
		1

		>>> ProcessUser.compareVersions('1.2.text', '1.2') # letters are > numbers 
		1

		>>> ProcessUser.compareVersions('10.2alpha1', '10.2alpha')
		1

		>>> ProcessUser.compareVersions('10.2dev', '10.2alpha') # letters are compared lexicographically
		1

		>>> ProcessUser.compareVersions('', '')
		0

		>>> ProcessUser.compareVersions('1', '')
		1

		@param v1: A string containing a version number, with any number of components. 
		@param v2: A string containing a version number, with any number of components. 

		@return: an integer > 0 if v1>v2, 
		an integer < 0 if v1<v2, 
		or 0 if they are semantically the same.
		"""
		return compareVersions(v1, v2)

	def write_text(self, file, text, encoding=None):
		"""
		Writes the specified text to a file in the output directory. 
		
		@param file: The path of the file to write, either an absolute path or 
			relative to the `self.output` directory. 
		
		@param text: The string to write to the file, with `\\n` 
			for newlines (do not use `os.linesep` as the file will be opened in 
			text mode so platform line separators will be added automatically).
			
			On Python 3 this must be a character string. 
			
			On Python 2 this can be a character or byte string containing ASCII 
			characters. If non-ASCII characters are used, it must be a unicode 
			string if there is an encoding specified for this file/type, or 
			else a byte string. 
		
		@param encoding: The encoding to use to open the file. 
			The default value is None which indicates that the decision will be delegated 
			to the L{getDefaultFileEncoding()} method. 
		"""
		# This method provides similar functionality to the Python3 pathlib write_text method. 
		
		with openfile(os.path.join(self.output, file), 'w', encoding=encoding or self.getDefaultFileEncoding(file)) as f:
			f.write(text)
	
	def copy(self, src, dest, mappers=[], encoding=None):
		"""Copy a single text or binary file, optionally tranforming the 
		contents by filtering each line through a list of mapping functions. 
		
		If any mappers are provided, the file is copied in text mode and 
		each mapper is given the chance to modify or omit each line. 
		If no mappers are provided, the file is copied in binary mode. 
		
		In addition to the file contents the mode is also copied, for example 
		the executable permission will be retained. 
		
		This function is useful both for creating a modified version of an 
		output file that's more suitable for later validation steps such as 
		diff-ing, and also for copying required files from the input to the 
		output directory. 
		
		For example::
		
			self.copy('output-raw.txt', 'output-processed.txt', encoding='utf-8', 
				mappers=[
					lambda line: None if ('Timestamp: ' in line) else line, 
					lambda line: line.replace('foo', 'bar'), 
				])
		
		@param src: The source filename, which can be an absolute path, or 
		a path relative to the `self.output` directory. 
		Use `src=self.input+'/myfile'` if you wish to copy a file from the test 
		input directory. 
		
		@param dest: The source filename, which can be an absolute path, or 
		a path relative to the `self.output` directory. If this is a directory 
		name, the file is copied to this directory with the same basename as src. 
		
		@param mappers: A list of filter functions that will be applied, 
		in order, to each line read from the file. Each function accepts a string for 
		the current line as input and returns either a string to write or 
		None if the line is to be omitted. 
		
		@param encoding: The encoding to use to open the file. 
		The default value is None which indicates that the decision will be delegated 
		to the L{getDefaultFileEncoding()} method. 
		"""
		src = toLongPathSafe(os.path.join(self.output, src))
		dest = toLongPathSafe(os.path.join(self.output, dest))
		if os.path.isdir(dest): dest = toLongPathSafe(dest+'/'+os.path.basename(src))
		assert src != dest, 'Source and destination file cannot be the same'
		
		if not mappers:
			# simple binary copy
			shutil.copyfile(src, dest)
		else:
			with openfile(src, 'r', encoding=encoding or self.getDefaultFileEncoding(src)) as srcf:
				with openfile(dest, 'w', encoding=encoding or self.getDefaultFileEncoding(dest)) as destf:
					for line in srcf:
						for mapper in mappers:
							line = mapper(line)
							if line is None: break
						if line is not None: destf.write(line)
			
		shutil.copymode(src, dest)
		