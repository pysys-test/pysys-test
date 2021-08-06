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
File copy function.

:meta private: Hidden from 1.5.1 onwards; shutil.copyfile should be used instead. 
"""


import shutil
import sys, os
from pysys.exceptions import *
from pysys.utils.fileutils import toLongPathSafe, pathexists

def copyfileobj(fsrc, fdst, length=16*1024):
	"""Internal method to read bytes from a source file descriptor, and write to a destination file descriptor.
	
	:param fsrc: The source file descriptor
	:param fdst: The destination file descriptor
	:param length: The buffer length to read from the src and write to the destination
	
	"""
	while 1:
		buf = fsrc.read(length)
		if not buf:
			break
		fdst.write(buf)


def filecopy(src, dst):
	"""Copy source file to a destination file.
	
	:param src: Full path to the source filename
	:param dst: Full path the destination filename
 	:raises FileNotFoundException: Raised if the source file does not exist
 
	"""
	if not pathexists(src):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(src)))
	
	shutil.copyfile(toLongPathSafe(src), toLongPathSafe(dst))


# entry point for running the script as an executable
if __name__ == "__main__":  # pragma: no cover (undocumented, little used executable entry point)
	if len(sys.argv) < 2:
		print("Usage: filecopy <src> <dst>")
		sys.exit()
	else:
		filecopy(sys.argv[1], sys.argv[2])

