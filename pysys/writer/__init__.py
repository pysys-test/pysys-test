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
Writers are configurable plugins responsible for summarising test results or processing test output as each test 
completes, or at the end when all tests has completed. 

"""

from pysys.utils.logutils import ColorLogFormatter, stripANSIEscapeCodes, stdoutPrint

# import into the writers.XXX package for the benefit of pre-1.6.0 project configs
from pysys.writer.api import *
from pysys.writer.ci import *
from pysys.writer.testoutput import *
from pysys.writer.outcomes import *
from pysys.writer.console import *
