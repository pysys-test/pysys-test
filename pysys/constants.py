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
Defines global constants that are used throughout the PySys framework. 

The standard convention is to import all contents of the module so that the constants can 
be referenced directly. 

@undocumented: ENVSEPERATOR, SITE_PACKAGES_DIR, DEFAULT_STYLESHEET, TRUE, FALSE, loadproject, PROJECT
"""
import sys, re, os, os.path, socket, traceback

# if set is not available (>python 2.6) fall back to the sets module
try:  
	set  
except NameError:  
	import sets
	from sets import Set as set

from pysys import stdoutHandler
from pysys.utils.pycompat import Enum

# set the platform and platform related constants
HOSTNAME = socket.getfqdn()
""" The fully qualified name of this host. """

if re.search('win32', sys.platform):
	PLATFORM='win32'
	"""OS platform - current values are: `linux`, `win32` (Windows), `sunos` (Solaris), `darwin` (Mac). """
	OSFAMILY='windows'
	DEVNULL = 'nul'
	WINDIR = os.getenv('windir', 'c:\WINDOWS')
	PATH = r'%s;%s\system32;%s\System32\Wbem' % (WINDIR, WINDIR, WINDIR)
	LD_LIBRARY_PATH = ''
	DYLD_LIBRARY_PATH = ''
	LIBRARY_PATH_ENV_VAR = 'PATH'
	SITE_PACKAGES_DIR =  os.path.join(sys.prefix, "Lib", "site-packages")
	
elif re.search('sunos', sys.platform): # pragma: no cover
	PLATFORM='sunos'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/ccs/bin:/usr/openwin/bin:/opt/SUNWspro/bin'
	LD_LIBRARY_PATH = '/usr/local/lib' 
	DYLD_LIBRARY_PATH = ''
	LIBRARY_PATH_ENV_VAR = 'LD_LIBRARY_PATH'
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

elif re.search('linux', sys.platform):
	PLATFORM='linux'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = '/usr/lib'
	DYLD_LIBRARY_PATH = ''
	LIBRARY_PATH_ENV_VAR = 'LD_LIBRARY_PATH'
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

elif re.search('darwin', sys.platform):
	PLATFORM='darwin'
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = ''
	DYLD_LIBRARY_PATH = '/usr/lib:/usr/local/lib'
	LIBRARY_PATH_ENV_VAR = 'DYLD_LIBRARY_PATH'
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")
else:  # pragma: no cover
	# Fall back to assumed UNIX-like platform
	PLATFORM=sys.platform
	OSFAMILY='unix'
	DEVNULL = '/dev/null'
	PATH = '/bin:/usr/bin:/usr/sbin:/usr/local/bin'
	LD_LIBRARY_PATH = '/usr/lib'
	DYLD_LIBRARY_PATH = ''
	LIBRARY_PATH_ENV_VAR = 'LD_LIBRARY_PATH'
	SITE_PACKAGES_DIR = os.path.join(sys.prefix, "lib", "python%s" % sys.version[:3], "site-packages")

ENVSEPERATOR = os.pathsep
""" Deprecated. 
@deprecated: use C{os.pathsep} instead. """

IS_WINDOWS = OSFAMILY=='windows'
""" True if this is Windows, False for other operating systems such as Unix. """

# constants used in testing
TRUE=True 
""" Deprecated. 
@deprecated: use True instead. """
FALSE=False
""" Deprecated. 
@deprecated: use False instead. """
BACKGROUND = 10
"""Constant indicating a process is to be started asynchronously in the background. """
FOREGROUND = 11
"""Constant indicating a process is to be run synchronously in the foreground. """

# outcomes
PASSED = 20
""" Non-failure test outcome indicating successful validation steps. """
INSPECT = 21
""" Non-failure test outcome indicating that manual inspection of the test output is required (in addition to any automated checks). """
NOTVERIFIED = 22
""" Non-failure test outcome indicating that it was not possible to positively validate correct operation. This is not treated as a failure outcome. """
FAILED = 23
""" Failure test outcome indicating validation steps with a negative outcome. """
TIMEDOUT = 24
""" Failure test outcome indicating that the test timed out while performing execution or validation operations. """
DUMPEDCORE = 25
""" Failure test outcome indicating that a crash occurred, and a `core` file was generated (UNIX only). """
BLOCKED = 26
""" Failure test outcome indicating that something went wrong, for example an exception was raised by the testcase or a required file could not be found. """
SKIPPED = 27
""" Non-failure test outcome indicating that the test was ignored as it is not currently required to run on this platform/mode. 
	See L{pysys.process.user.ProcessUser.skipTest}.
"""

LOOKUP = {}
"""Lookup dictionary providing the string representation of test outcomes.
"""
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
""" Lists all test outcomes in order of precedence. If a test has multiple outcomes, 
the one that appears first in this list takes precedence over any other. """
FAILS = [ BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED ]
""" Lists the test outcomes treated as failure. 
Outcomes such as L{NOTVERIFIED} and L{SKIPPED} are not considered failures. """

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
DEFAULT_FORMAT = u'%(asctime)s %(levelname)-5s %(message)s'
DEFAULT_ABORT_ON_ERROR=False

OSWALK_IGNORES = [ DEFAULT_INPUT, DEFAULT_OUTPUT, DEFAULT_REFERENCE, 'CVS', '.svn', '__pycache__', '.git' ]
""" A list of directory names to exclude when recursively walking a directory tree. """

DEFAULT_TIMEOUT = 600
"""Deprecated. 
@deprecated: Use a specific member of TIMEOUTS instead."""
TIMEOUTS = {}
""" Default timeouts used for various operations. 

Each timeout is given as a floating point number of seconds.

These timeouts can be customized from runner.setup() if needed 
(but never change them from within individual testcases). 
 """
TIMEOUTS['WaitForSocket'] = 60
TIMEOUTS['WaitForFile'] = 30
TIMEOUTS['WaitForSignal'] = 60
TIMEOUTS['WaitForProcessStop'] = 30
TIMEOUTS['WaitForProcess'] = 60*10
TIMEOUTS['WaitForAvailableTCPPort'] = 60*20 # in case other tests are using up all ports
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

class PrintLogs(Enum):
	"""Enumeration constants that specify when run.log contents are printed to the stdout console.
	
	In all cases a summary of failures is printed at the end, and the user can always 
	look at the run.log inside each output directory if they need more detail. 
	"""
	NONE = 'PrintLogs.NONE'
	"""Detailed run.log output is not printed to the stdout console. """
	ALL = 'PrintLogs.ALL'
	"""Detailed run.log output is always printed to the stdout console, for both passed and failed testcases. """
	FAILURES = 'PrintLogs.FAILURES'
	"""Detailed run.log output is only printed to the stdout console for failed testcases. """

PROJECT = None
"""DEPRECATED. 
Holds the L{pysys.xml.project.Project} instance containing settings for this PySys project.
Instead of using this constant, we recommend using the 
L{pysys.basetest.BaseTest.project} (or L{pysys.process.user.ProcessUser.project}) 
field to access this. If this is not possible, use Project.getInstance(). """

from pysys.xml.project import Project 
def loadproject(start):
	global PROJECT
	Project.findAndLoadProject(start)
	PROJECT = Project.getInstance()