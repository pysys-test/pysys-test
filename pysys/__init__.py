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
PySys System Test Framework.

PySys has been designed to provide a generic extensible multi-threaded framework for the organisation and execution of system 
level testcases. It provides a clear model of what a testcases is, how it is structured on disk, how it is executed and validated, 
and how the outcome is reported for test auditing purposes. 

Testcases are instances of a base test class (L{pysys.basetest.BaseTest}) which provides core functionality for cross platform 
process management, monitoring and manipulation; in this manner an application under test (AUT) can be started and interacted with 
directly within a testcase. The base test class additionally provides a set of standard validation techniques based predominantly 
on regular expression matching within text files (e.g. stdout, logfile of the AUT etc). Testcases are executed through a base 
runner (L{pysys.baserunner.BaseRunner}) which provides the mechanism to control concurrent testcase flow and auditing. In both 
cases the base test and runner classes have been designed to be extended for a particular AUT, e.g. to allow a higher level of 
abstraction over the AUT, tear up and tear down prior to executing a set of testcases etc. 

PySys allows automated regression testcases to be built rapidly. Where an AUT cannot be tested in an automated fashion, testcases 
can be written to make use of a manual test user interface (L{pysys.manual.ui.ManualTester}) which allows the steps required to 
execute the test to be presented to a tester in a concise and navigable manner. The tight integration of both manual and automated 
testcases provides a single framework for all test organisation requirements. 

@undocumented: ThreadedStreamHandler, ThreadedFileHandler
"""

import sys, logging, threading

__author__  = "Moray Grieve"
"""The original author of PySys."""

__maintainer__  = "Ben Spiller"
"""The current lead maintainer of PySys."""

__maintainer_email__ = "pysys-dev@googlegroups.com"
"""The maintainer e-mail address."""

__status__  = "Production"
"""The status of this release."""

__version__ = "1.4.0.dev1"
"""The version of this release."""

__date__ = "yyyy-mm-dd"
"""The date of this release."""

__license__ = "GNU Lesser General Public License"
"""The PySys license."""

__all__     = [ "constants",
                "exceptions",
                "baserunner",
                "basetest",
                "interfaces",
                "launcher",
                "manual",
                "process",
                "unit",
                "utils",
                "writer",
                "xml"]
"""The submodules of PySys."""

# Lock to be held when creating processes also while holding any resources
# we don't want being passed to child processes e.g. sockets, files
process_lock = threading.Lock()

# customize the default logging names for display
logging.addLevelName(50, 'CRIT')
logging.addLevelName(30, 'WARN')

# class extensions for supporting multi-threaded nature

from pysys.utils.pycompat import _UnicodeSafeStreamWrapper, PY2

class ThreadedStreamHandler(logging.StreamHandler):
	"""Stream handler to only log from the creating thread.
	
	Overrides logging.StreamHandler to only allow logging to a stream 
	from the thread that created the class instance and added to the root 
	logger via log.addHandler(ThreadedStreamHandler(stream)).

	This is used to pass log output from the specific test that creates this 
	handler to stdout, either immediately or (when multiple threads are in use) 
	at the end of each test's execution. 
	
	@deprecated: For internal use only, do not use. 
	"""
	def __init__(self, strm=None, streamFactory=None):
		"""Overrides logging.StreamHandler.__init__.
		@param strm: the stream
		@param streamFactory: a function that returns the stream, if strm is not specified. 
		"""
		self.threadId = threading.current_thread().ident
		self.__streamfactory = streamFactory if streamFactory else (lambda:strm)
		logging.StreamHandler.__init__(self, self.__streamfactory())
		
	def emit(self, record):
		"""Overrides logging.StreamHandler.emit."""
		if self.threadId != threading.current_thread().ident: return
		logging.StreamHandler.emit(self, record)

	def _updateUnderlyingStream(self):
		""" Update the stream this handler uses by calling again the stream factory; 
		used only for testing. 
		"""
		assert self.stream # otherwise assigning to it wouldn't do anything
		self.stream = self.__streamfactory()
		
class ThreadedFileHandler(logging.FileHandler):
	"""File handler to only log from the creating thread.
	
	Overrides logging.FileHandler to only allow logging to file from 
	the thread than created the class instance and added to the root 
	logger via log.addHandler(ThreadFileHandler(filename)).
	
	This is used to pass log output from the specific test 
	that creates this handler to the associated run.log. 

	@deprecated: No longer used, will be removed. 
	"""
	def __init__(self, filename, encoding=None):
		"""Overrides logging.FileHandler.__init__"""
		self.threadId = threading.current_thread().ident
		logging.FileHandler.__init__(self, filename, "a", encoding=self.__streamencoding)

	def emit(self, record):
		"""Overrides logging.FileHandler.emit."""
		if self.threadId != threading.current_thread().ident: return
		# must put formatted messages into the buffer otherwise we lose log level 
		# and (critically) exception tracebacks from the output
		logging.FileHandler.emit(self, record)
		

class ThreadFilter(logging.Filterer):
	"""Filter to disallow log records from the current thread.
	
	Within pysys, logging to standard output is only enabled from the main thread 
	of execution (that in which the test runner class executes). When running with
	more than one test worker thread, logging to file of the test run log is 
	performed through a file handler, which only allows logging from that thread. 
	To disable either of these, use an instance of this class from the thread in 
	question, adding to the root logger via log.addFilter(ThreadFilter()).
	
	"""
	def __init__(self):
		"""Overrides logging.Filterer.__init__"""
		self.threadId = threading.current_thread().ident
		logging.Filterer.__init__(self)
		
	def filter(self, record):
		"""Implementation of logging.Filterer.filter to block from the creating thread."""
		if self.threadId != threading.current_thread().ident: return True
		return False
	

rootLogger = logging.getLogger('pysys')
"""The root logger for all logging within PySys."""

rootLogger.setLevel(logging.DEBUG)
"""The root logger log level (set to DEBUG as all filtering is done by the handlers)."""

stdoutHandler = ThreadedStreamHandler(streamFactory=lambda: _UnicodeSafeStreamWrapper(sys.stdout, writebytes=PY2))
"""The default stdout logging handler for all logging within PySys."""

# see also pysys.py for logging configuration

# global reference is using log
log = rootLogger
