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

import os
import sys, time
sys.stderr.write(f'Time = {time.time()} main.py\n')
sys.stderr.write(' = '+time.strftime("%a %Y-%m-%d %H:%M:%S %Z", time.localtime( time.time() ))+"\n") # local time in friendly format
 

if sys.version_info[0] < 3:
	sys.stderr.write('This version of PySys requires Python 3; if you need Python 2 support, you must use an older version of PySys such as v1.6.1\n')
	sys.exit(100)

import pysys
sys.stderr.write(f'Time = {time.time()} imported pysys\n')
import logging
sys.stderr.write(f'Time = {time.time()} imported logging\n')

def main(args=None):
	"""The entry-point for invoking PySys."""
	
	if args is None: args = sys.argv[1:]
	sys.stderr.write(f'Time = {time.time()} about to import console\n')

	import pysys.launcher.console
	sys.stderr.write(f'Time = {time.time()} imported console\n')
	return pysys.launcher.console.main(args)
if __name__ == "__main__": 
	main()
