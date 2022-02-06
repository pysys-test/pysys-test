#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2022 M.B. Grieve

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
Old module for performance reporter - deprecated in favour of `pysys.perf`.

Deprecated in PySys v2.1. 

"""

import collections, threading, time, math, sys, os
import io
import logging

if __name__ == "__main__":
	sys.path.append(os.path.dirname( __file__)+'/../..')

from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *

from pysys.perf.perfreportstool import perfReportsToolMain

# For backwards compatibility where modules are importing this
from pysys.perf.reporters import *
from pysys.perf.api import PerformanceUnit

if __name__ == "__main__":
	perfReportsToolMain(sys.argv[1:])
