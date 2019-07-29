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
PySys System Test Framework.

PySys is an easy-to-use cross-platform framework for writing and orchestrating 
all your system/integration tests, combined seamlessly with your unit and 
manual tests. 

It provides a comprehensive package of utility methods to make all the common 
system/integration testing operations a breeze, as well as the flexibility to 
add whatever test execution and validation logic you need using the full power 
of the Python language. 

For more information see https://pypi.org/project/PySys/

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

"""

__author__  = "Moray Grieve, Ben Spiller"
"""The original creator, and subsequent lead maintainer(s) of PySys."""

__maintainer__  = "Ben Spiller"
"""The current lead maintainer of PySys."""

__maintainer_email__ = "pysys-dev@googlegroups.com"
"""The maintainer e-mail address."""

__status__  = "Production"
"""The status of this release."""

__version__ = "1.5.0"
"""The version of this release."""

__date__ = "yyyy-mm-dd"
"""The date of this release."""

__license__ = "GNU Lesser General Public License"
"""The PySys license."""

__all__  = [
	"constants",
	"exceptions",
	"baserunner",
	"basetest",
	"launcher",
	"manual",
	"process",
	"unit",
	"utils",
	"writer",
	"xml"
]
"""The public submodules of PySys."""

# initialize the Python logging system for PySys
from pysys.internal.initlogging import rootLogger, stdoutHandler, log
from pysys.internal.initlogging import ThreadedStreamHandler, ThreadedFileHandler, ThreadFilter

import threading
process_lock = threading.Lock()
""" Lock to be held when creating processes also while holding any resources
we don't want being passed to child processes e.g. sockets, files. """
