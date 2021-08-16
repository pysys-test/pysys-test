#!/usr/bin/env python
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
Standard constants that are used throughout the PySys framework. 

The convention is to import all contents of the module so that the constants can 
be referenced directly. 

"""
# undocumented (no longer in public API): ENVSEPERATOR, SITE_PACKAGES_DIR, DEFAULT_STYLESHEET, TRUE, FALSE, PROJECT

import sys, re, os, os.path, socket, traceback, locale
from enum import Enum

from pysys import stdoutHandler

# set the platform and platform related constants
HOSTNAME = socket.getfqdn()
""" The fully qualified name of this host. """

if re.search('win32', sys.platform):
	PLATFORM='win32'
	"""OS platform - current values are: `linux`, `win32` (Windows), `sunos` (Solaris), `darwin` (Mac). 
	It is recommended to use standard Python functions such as ``sys.platform`` rather than this constant. """
	OSFAMILY='windows'
	DEVNULL = 'nul'
	WINDIR = os.getenv('windir', r'c:\WINDOWS')
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
	DYLD_LIBRARY_PATH = '$(HOME)/lib:/usr/local/lib:/lib:/usr/lib'
	LIBRARY_PATH_ENV_VAR = 'DYLD_FALLBACK_LIBRARY_PATH'
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

PREFERRED_ENCODING = locale.getpreferredencoding()
"""
The operating system's preferred/default encoding for reading/writing the contents of text data in files and 
process stdout/stderr for the current environment (or machine). 

This returns the same value as Python's ``locale.getpreferredencoding()`` method, but as that method is not thread-safe, 
this constant must always be used in test cases to avoid race conditions when running tests in parallel. 

The OS preferred encoding should not be confused with Python's 'default' encoding (``sys.getdefaultencoding()``) which 
is usually not relevant for testing purposes. 

See also `pysys.basetest.BaseTest.getDefaultFileEncoding()`.

.. versionadded:: 2.0
"""

ENVSEPERATOR = os.pathsep
""" Deprecated. 
:meta private: Use ``os.pathsep`` instead. """

IS_WINDOWS = OSFAMILY=='windows'
""" True if this is Windows, False for other operating systems such as Unix. """

PYTHON_EXE = sys.executable # alias to increase readability
"""
The path to the current Python executable (=``sys.executable``). 
"""

EXE_SUFFIX = '.exe' if IS_WINDOWS else ''
""" The suffix added to binary executables, that is ``.exe`` on Windows, and empty string on Unix. 
"""

# constants used in testing
TRUE=True 
""" Deprecated. 
:meta private: use True instead. """
FALSE=False
""" Deprecated. 
:meta private: use False instead. """
BACKGROUND = 10
"""Constant indicating a process is to be started asynchronously in the background. """
FOREGROUND = 11
"""Constant indicating a process is to be run synchronously in the foreground. """

# outcomes
class Outcome:
	"""Represents a PySys test outcome that can be reported using `pysys.basetest.BaseTest.addOutcome()`. 
	
	The possible outcomes are listed in `OUTCOMES`. 
	
	Use ``str()`` or ``%s`` to get the display name for an outcome (e.g. "TIMED OUT"), and `isFailure()` to check 
	if it's a failure outcome. 
	"""
	__alreadyInstantiated = set()
	def __init__(self, id, isFailure, displayName=None):
		displayName = (displayName or id).upper()
		assert displayName not in Outcome.__alreadyInstantiated # avoid duplicate instances, since we use reference equality to compare these
		Outcome.__alreadyInstantiated.add(displayName)
		self.__id, self.__name, self.__isFailure = id, displayName, isFailure
	def __repr__(self): return '%s%s'%(self.__id, ('' if self.__isFailure else '(non-failure)')) # use the constant id for this __repr__ string that shows in the doc
	def __str__(self): return self.__name
	def isFailure(self): 
		""":return bool: True if this outcome is classed as failure, or False if not (e.g. `SKIPPED` and `NOTVERIFIED` are not failures).""" 
		return self.__isFailure

PASSED = Outcome('PASSED', isFailure=False)
""" Non-failure test `Outcome` indicating successful validation steps. """
INSPECT = Outcome('INSPECT', isFailure=False, displayName='REQUIRES INSPECTION')
""" Non-failure test `Outcome` indicating that manual inspection of the test output is required (in addition to any automated checks). """
NOTVERIFIED = Outcome('NOTVERIFIED', isFailure=False, displayName='NOT VERIFIED')
""" Non-failure test `Outcome` indicating that it was not possible to positively validate correct operation. This is not treated as a failure outcome. """
FAILED = Outcome('FAILED', isFailure=True)
""" Failure test `Outcome` indicating validation steps with a negative outcome. """
TIMEDOUT = Outcome('TIMEDOUT', isFailure=True, displayName='TIMED OUT')
""" Failure test `Outcome` indicating that the test timed out while performing execution or validation operations. """
DUMPEDCORE = Outcome('DUMPEDCORE', isFailure=True, displayName='DUMPED CORE')
""" Failure test `Outcome` indicating that a crash occurred, and a `core` file was generated (UNIX only). """
BLOCKED = Outcome('BLOCKED', isFailure=True)
""" Failure test `Outcome` indicating that something went wrong, for example an exception was raised by the testcase or a required file could not be found. """
SKIPPED = Outcome('SKIPPED', isFailure=False)
""" Non-failure test `Outcome` indicating that the test was ignored as it is not currently required to run on this platform/mode. 
	See `pysys.basetest.BaseTest.skipTest`.
"""


# set the precedent for the test outcomes
OUTCOMES = (SKIPPED, BLOCKED, DUMPEDCORE, TIMEDOUT, FAILED, NOTVERIFIED, INSPECT, PASSED)
"""
Lists all possible test outcomes, in descending order of precedence. 

.. autosummary::
	SKIPPED
	BLOCKED
	DUMPEDCORE
	TIMEDOUT
	FAILED
	NOTVERIFIED
	INSPECT
	PASSED

If a test adds multiple outcomes, the outcome with highest precedence is used as the final test outcome 
(i.e. SKIPPED rather than FAILED, FAILED rather than PASSED etc). 

Each item is an instance of `Outcome`. Use `Outcome.isFailure()` to check whether a given outcome is classed as a failure for reporting purposes. 

"""
PRECEDENT = OUTCOMES
""":deprecated: The old name for `OUTCOMES`.  """
FAILS = [__outcome for __outcome in OUTCOMES if __outcome.isFailure() ]
""":deprecated: To test whether a specific outcome from OUTCOMES is a failure, use `Outcome.isFailure()`. """


LOOKUP = {__outcome: str(__outcome) for __outcome in OUTCOMES}
"""Lookup dictionary providing the string representation of test outcomes.
:deprecated: Use ``str(outcome)`` on the `Outcome` to convert to the display name. 
"""
LOOKUP[True] = "TRUE"
LOOKUP[False] = "FALSE"
LOOKUP[TRUE] = "TRUE"
LOOKUP[FALSE] = "FALSE"

# set the default descriptor filename, input, output and reference directory names
DEFAULT_PROJECTFILE = ['pysysproject.xml']
DEFAULT_DESCRIPTOR = ['pysystest.xml'] # deprecated, do not use this. For customization use the pysysTestDescriptorFileNames project property. 
DEFAULT_MODULE = 'run.py' # deprecated, do not use this. 
DEFAULT_GROUP = ""
DEFAULT_TESTCLASS = 'PySysTest'
DEFAULT_INPUT = 'Input'
DEFAULT_OUTPUT = 'Output'
DEFAULT_REFERENCE = 'Reference'
DEFAULT_RUNNER = 'pysys.baserunner.BaseRunner'
DEFAULT_MAKER = 'pysys.launcher.console.DefaultTestMaker'
DEFAULT_STYLESHEET = None # deprecated
DEFAULT_FORMAT = u'%(asctime)s %(levelname)-5s %(message)s'
DEFAULT_OUTDIR = 'win' if PLATFORM=='win32' else PLATFORM # this constant is not currently public API

OSWALK_IGNORES = [ '.git', '.svn', '__pycache__', 'CVS', ]
""" A list of directory names to exclude when recursively walking a directory tree. 

This is used by PySys during test loading, and can also be used for subsequent directory walking operations. 
"""

DEFAULT_TIMEOUT = 600
"""Deprecated: Use a specific member of `TIMEOUTS` instead."""
TIMEOUTS = {}
""" Default timeouts used for various operations. 

Each timeout is given as a floating point number of seconds.

These timeouts can be customized from a runner plugin (or `pysys.baserunner.BaseRunner.setup()`) if needed 
(but never change them from within individual testcases). 
 """
TIMEOUTS['WaitForSocket'] = 60
TIMEOUTS['WaitForFile'] = 30
TIMEOUTS['WaitForSignal'] = 60
TIMEOUTS['WaitForProcessStop'] = 30
TIMEOUTS['WaitForProcess'] = 60*10
TIMEOUTS['WaitForAvailableTCPPort'] = 60*5 # in case other tests are using up all ports
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
LOG_DIFF_ADDED = 'diff+'
LOG_DIFF_REMOVED = 'diff-'
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
""":meta private: Hide this since 1.5.1 since we don't want people to use it. 

Holds the L{pysys.config.project.Project} instance containing settings for this PySys project.
Instead of using this constant, use `pysys.basetest.BaseTest.project` (or`pysys.process.user.ProcessUser.project`) 
field to access this. If this is not possible, use Project.getInstance().

This is set by the console_XXX modules when the project is loaded. 
"""
from pysys.config.project import Project # retained for compatibility when using 'from constants import *'
