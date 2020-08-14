#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA



"""
Welcome to the PySys System Test Framework.

`pysys.basetest` contains (or provides links to) pretty much everything you need for the main business of creating 
testcases using PySys.

However for more advanced users, it is possible to customize many aspects of PySys behaviour by providing custom 
implementations of PySys classes described in this API reference:

	- `pysys.baserunner.BaseRunner` to customize orchestration of all the tests in a test run. 
	- `pysys.writer` classes to customize how test outcomes are recorded.
	- `pysys.utils.perfreporter.CSVPerformanceReporter` to customize how numeric performance results are reported.
	- `pysys.xml.descriptor.DescriptorLoader` to customize how PySys find and runs tests (e.g. to support running tests 
	  from other frameworks within PySys). 
	- `pysys.utils.logutils.BaseLogFormatter` for advanced customization of log message format.

There are also many utility functions which could be helpful when creating custom assertion methods. However before 
using any functions from `pysys.utils`, always check first if there is a more convenient method available to do the 
job on `pysys.basetest.BaseTest`/`pysys.baserunner.BaseRunner`. 

"""

__author__  = "Moray Grieve, Ben Spiller"
"""The original creator, and subsequent lead maintainer(s) of PySys."""

__maintainer__  = "Ben Spiller"
"""The current lead maintainer of PySys."""

__maintainer_email__ = "pysys-dev@googlegroups.com"
"""The maintainer e-mail address."""

__status__  = "Production"
"""The status of this release."""

__version__ = "1.6.2.dev1"
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
from pysys.internal.initlogging import ThreadFilter # for compatibility

import threading
process_lock = threading.Lock()
""" Lock to be held when creating processes also while holding any resources
we don't want being passed to child processes e.g. sockets, files. """
