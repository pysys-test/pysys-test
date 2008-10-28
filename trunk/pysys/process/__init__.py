#!/usr/bin/env python
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and any associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use, copy,
# modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# The software is provided "as is", without warranty of any
# kind, express or implied, including but not limited to the
# warranties of merchantability, fitness for a particular purpose
# and noninfringement. In no event shall the authors or copyright
# holders be liable for any claim, damages or other liability,
# whether in an action of contract, tort or otherwise, arising from,
# out of or in connection with the software or the use or other
# dealings in the software
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

import os.path
from pysys.constants import *

# set the modules to import when imported the pysys.process package
__all__ = [ "helper",
			"monitor",
			"user" ]

# add to the __path__ to import the platform specific helper class
dirname = __path__[0]
if PLATFORM in [ "sunos", "linux" ]:
	__path__.append(os.path.join(dirname, "plat-unix"))
else:
	__path__.append(os.path.join(dirname, "plat-win32"))



