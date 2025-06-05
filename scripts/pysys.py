#!/usr/bin/env python3
# PySys System Test Framework, Copyright (C) 2006-2023 M.B. Grieve

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


if __name__ == "__main__": 
	# the sys.path starts with the directory containing pysys.py which can lead to Python 
	# mistaking this file for the pysys package; regardless, it's not needed for locating 
	# the pysys modules since those will be in site-packages once pysys is installed
	import os, sys, time
	sys.stderr.write(f'Time = {time.time()} at entrypoint\n')

	script_path = os.path.normcase(os.path.abspath(sys.path[0]))
	sys.path = [p for p in sys.path if os.path.normcase(os.path.abspath(p)) != script_path]

	from pysys import __main__
	__main__.main()
