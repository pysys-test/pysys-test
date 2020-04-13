#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2020 M.B. Grieve, Ben Spiller

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
Welcome to the PySys System Test Framework.

`pysys.basetest` contains (or provides links to) pretty much everything you need for the main business of creating 
testcases using PySys.

However for more advanced users, it is possible to customize many aspects of PySys behaviour by providing custom 
implementations of PySys classes described in this API reference (e.g. `pysys.baserunner.BaseRunner`). There are also 
many utility functions which could be helpful when creating custom assertion methods. 

"""

__author__  = "Moray Grieve, Ben Spiller"
"""The original creator, and subsequent lead maintainer(s) of PySys."""

__maintainer__  = "Ben Spiller"
"""The current lead maintainer of PySys."""

__maintainer_email__ = "pysys-dev@googlegroups.com"
"""The maintainer e-mail address."""

__status__  = "Production"
"""The status of this release."""

__version__ = "1.5.1.dev1"
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
