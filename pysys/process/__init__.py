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
Contains cross platform classes and utilities for starting, stopping and monitoring processes. 

The module contains the base class L{pysys.process.user} that can be extended by subclasses that 
require the ability to start, stop, interact and monitor processes started by the PySys 
framework. Subclasses within the framework are the L{pysys.basetest.BaseTest} and 
L{pysys.baserunner.BaseRunner} classes, both of which may be required to start processes as part 
of the execution of a set of testcases. The import path of the helper and monitor modules is set up
at runtime so as to select either the Win32 modules (located in pysys.process.plat-win32), or the 
unix modules (located in pysys.process.plat-unix); both modules are written to display common 
functionality in order to provide a unified abstraction where the user is not required to select the 
correct modules based on their current operation system.

"""

from pysys.constants import *

# set the modules to import when imported the pysys.process package
__all__ = [ "helper",
			"monitor", 
			"monitorimpl",
			"user" ]

# add to the __path__ to import the platform specific helper class
dirname = __path__[0]
if PLATFORM in [ "win32" ]:
	__path__.append(os.path.join(dirname, "plat-win32"))
else:
	__path__.append(os.path.join(dirname, "plat-unix"))



