#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2018  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net
"""
Defines global constants that are used throughout the PySys framework. 

The standard convention is to import all contents of the module so that the constants can 
be referenced directly. The module also contains methods for locating and parsing the PySys 
project file (L{pysys.constants.loadproject}), and the project class that provides an 
abstraction over the contents of the file (L{pysys.constants.Project}). For more information 
about the structure and contents of the project file, see the PySys examples 
distribution. 

"""
import sys, re, os, os.path, socket, traceback

# if set is not available (>python 2.6) fall back to the sets module
try:  
	set  
except NameError:  
	import sets
	from sets import Set as set

from pysys import stdoutHandler

# set the platform and platform related constants
HOSTNAME = socket.getfqdn()
if re.search('win32', sys.platform):
	PLATFORM='win32'	
	OSFAMILY='windows'
	DEVNULL = 'nul'
	WINDIR = os.getenv('windir', 'c:\WINDOWS')
	PATH = r'%s;%s\system32;%s\System32\Wbem' % (WINDIR, WINDIR, WINDIR)
	LD_LIBRARY_PATH = ''
	DYLD_LIBRARY_PATH = ''
	SITE_PACKAGES_DIR =  os.path.join(sys.prefix, "Lib", "site-packages")
	
elif re.search('sunos', sys.platform):
	PLATFORM='sunos'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/ccs/bin:/usr/openwin/bin:/opt/SUNWspro/bin'
	LD_LIBRARY_PATH = '/usr/local/lib' 
	DYLD_LIBRARY_PATH = ''
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

elif re.search('linux', sys.platform):
	PLATFORM='linux'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = '/usr/lib'
	DYLD_LIBRARY_PATH = ''
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

elif re.search('darwin', sys.platform):
	PLATFORM='darwin'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = ''
	DYLD_LIBRARY_PATH = '/usr/lib:/usr/local/lib'
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

else:
	# Fall back to assumed UNIX-like platform
	PLATFORM=sys.platform
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = '/usr/lib'
	DYLD_LIBRARY_PATH = ''
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

ENVSEPERATOR = os.pathsep

IS_WINDOWS = OSFAMILY=='windows'

# constants used in testing
TRUE=True
FALSE=False
BACKGROUND = 10
FOREGROUND = 11
PASSED = 20
INSPECT = 21
NOTVERIFIED = 22
FAILED = 23
TIMEDOUT = 24
DUMPEDCORE = 25
BLOCKED = 26
SKIPPED = 27

LOOKUP = {}
LOOKUP[True] = "TRUE"
LOOKUP[False] = "FALSE"
LOOKUP[TRUE] = "TRUE"
LOOKUP[FALSE] = "FALSE"
LOOKUP[PASSED] = "PASSED"
LOOKUP[INSPECT] = "REQUIRES INSPECTION"
LOOKUP[NOTVERIFIED] = "NOT VERIFIED"
LOOKUP[FAILED] = "FAILED"
LOOKUP[TIMEDOUT] = "TIMED OUT"
LOOKUP[DUMPEDCORE] = "DUMPED CORE"
LOOKUP[BLOCKED] = "BLOCKED"
LOOKUP[SKIPPED] = "SKIPPED"

# set the precedent for the test outcomes
PRECEDENT = [SKIPPED, BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED, NOTVERIFIED, INSPECT, PASSED]
FAILS = [ BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED ]

# set the default descriptor filename, input, output and reference directory names
DEFAULT_PROJECTFILE = ['pysysproject.xml', '.pysysproject']
DEFAULT_DESCRIPTOR = ['pysystest.xml', '.pysystest', 'descriptor.xml']  
DEFAULT_MODULE = 'run'
DEFAULT_GROUP = ""
DEFAULT_TESTCLASS = 'PySysTest'
DEFAULT_INPUT = 'Input'
DEFAULT_OUTPUT = 'Output'
DEFAULT_REFERENCE = 'Reference'
DEFAULT_RUNNER =  ['BaseRunner', 'pysys.baserunner']
DEFAULT_MAKER =  ['ConsoleMakeTestHelper', 'pysys.launcher.console']
DEFAULT_WRITER =  ['XMLResultsWriter', 'pysys.writer', 'testsummary_%Y%m%d%H%M%S.xml', {}]
DEFAULT_STYLESHEET = None # deprecated
DEFAULT_FORMAT = '%(asctime)s %(levelname)-5s %(message)s'
DEFAULT_ABORT_ON_ERROR=False

# set the directories to not recursively walk when looking for the descriptors
OSWALK_IGNORES = [ DEFAULT_INPUT, DEFAULT_OUTPUT, DEFAULT_REFERENCE, 'CVS', '.svn', '__pycache__' ]

# set the timeout values for specific executables when executing a test
DEFAULT_TIMEOUT = 600
TIMEOUTS = {}
TIMEOUTS['WaitForSocket'] = 60
TIMEOUTS['WaitForFile'] = 30
TIMEOUTS['WaitForSignal'] = 60
TIMEOUTS['WaitForProcessStop'] = 30
TIMEOUTS['WaitForProcess'] = 60*10
TIMEOUTS['ManualTester'] = 1800

# the supported distinct log categories
LOG_WARN = 'warn'
LOG_ERROR = 'error'
LOG_DEBUG = 'debug'
LOG_TRACEBACK = 'traceback'
LOG_FILE_CONTENTS = 'filecontents'
LOG_TEST_DETAILS = 'details'
LOG_TEST_OUTCOMES = 'outcomereason'
LOG_TEST_PROGRESS = 'progress'
LOG_TEST_PERFORMANCE = 'performance'
LOG_TIMEOUTS = 'timed out'
LOG_FAILURES = 'failed'
LOG_PASSES = 'passed'
LOG_SKIPS = 'skipped'
LOG_END = 'end'

# reference to the project instance defining parameters for the 
# pysys project
PROJECT = None

from pysys.xml.project import Project 

# load the project specific details
def loadproject(start):
	"""Load the PySys project file.
	
	The method walks up the directory tree from the supplied path until the 
	PySys project file is found. The location of the project file defines
	the project root location. The contents of the project file determine 
	project specific constants as specified by property elements in the 
	xml project file.
	
	To ensure that all loaded modules have a pre-initialised projects 
	instance, any launching application should first import the loadproject
	file, and then make a call to it prior to importing all names within the
	constants module.

	@param start: The initial path to start from when trying to locate the project file

	"""

	global PROJECT

	projectFile = os.getenv('PYSYS_PROJECTFILE', None)
	search = start
	if not projectFile:
		projectFileSet = set(DEFAULT_PROJECTFILE)
		
		drive, path = os.path.splitdrive(search)
		while (not search == drive):
			intersection =  projectFileSet & set(os.listdir(search))
			if intersection : 
				projectFile = intersection.pop()
				break
			else:
				search, drop = os.path.split(search)
				if not drop: search = drive
	
		if not (projectFile is not None and os.path.exists(os.path.join(search, projectFile))):
			sys.stderr.write("WARNING: No project file found, taking project root to be '%s' \n" % (search or '.'))

	try:
		PROJECT = Project(search, projectFile)
		stdoutHandler.setFormatter(PROJECT.formatters.stdout)
	except Exception as e:
		sys.stderr.write("ERROR: Failed to load project due to %s - %s\n"%(e.__class__.__name__, e))
		traceback.print_exc()
		sys.exit(1)
