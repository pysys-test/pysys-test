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
Unpacking one or more compressed files. 

Deprecated - use `pysys.basetest.BaseTest.unpackArchive` instead. 
"""

from __future__ import print_function
import os.path, glob, gzip, shutil, re

from pysys.constants import *
from pysys.exceptions import *
from pysys.utils.fileutils import toLongPathSafe

def unzipall(path, binary=False):
	"""Unzip all .gz files in a given directory.
	
	Archive files are automatically deleted after unzipping. 
	
	:param path: The full path to the directory containing the archive files.
	:param binary: Boolean flag to indicate if the unzipped files should be written as binary. 
		The default value of False indicates that on some platforms newline characters will be 
		converted to the operating system default. 
	
	:raises FileNotFoundException: Raised if the directory path does not exist.
	
	"""
	if not os.path.exists(path):
		raise FileNotFoundException("%s path does not exist" % (os.path.basename(path)))

	for file in glob.glob('%s/*.gz'%(path)):
		unzip(file, True, binary)



def unzip(zfilename, replace=False, binary=False):
	"""Unzip a .gz archive and write the contents to disk.
	
	Deprecated - replace ``unzip(gzfilename, binary=True)`` with ``self.unpackArchive(gzfilename, gzfilename[:-3])``
	
	The method will unpack a file of the form C{file.data.gz} to C{file.data}, removing the 
	archive file in the process if the C{replace} input parameter is set to true. 
	
	By default the unpacked archive is treated as non-binary data, 
	unless the binary input parameter is set to true.
	
	:param zfilename: The full path to the archive file.
	:param replace: Boolean flag to indicate if the archive file should be removed after unpacking.
	:param binary: Boolean flag to indicate if the unzipped file should be written as binary.
		The default value of False indicates that on some platforms newline characters will be 
		converted to the operating system default. 
	
	:raises pysys.exceptions.FileNotFoundException: Raised if the archive file does not exist.
	:raises pysys.exceptions.IncorrectFileTypeEception: Raised if the archive file does not have a .gz extension.
	
	"""
	if not os.path.exists(zfilename):
		raise FileNotFoundException("unable to find file %s" % (os.path.basename(zfilename)))

	tokens	= zfilename.split('.')
	if tokens[len(tokens)-1] != 'gz':
		raise IncorrectFileTypeException("file does not have a .gz extension")
	
	uzfilename = ''
	for i in range(len(tokens)-1):
		uzfilename = uzfilename + tokens[i]
		if i != len(tokens)-2:
			uzfilename = uzfilename + '.'

	# must read and write in binary in all cases, since we don't know for 
	# certain what encoding it's in and want to avoid corrupting 
	# non-newline characters
	with gzip.GzipFile(toLongPathSafe(zfilename), 'rb', 9) as zfile:
		with open(toLongPathSafe(uzfilename), 'wb') as uzfile:
			if binary: 
				# do an efficient block-by-block copy, in case it's large
				shutil.copyfileobj(zfile, uzfile)
			else:
				# non-binary means fix newlines.
				# for compatibility with pre-1.3 PySys this is currently 
				# implemented for basic cases and only on windows. 
				buffer = zfile.read()
				if PLATFORM=='win32': buffer = buffer.replace(b'\n', b'\r\n')
				uzfile.write(buffer)

	if replace:
		try:
			os.remove(zfilename)
		except OSError:
			pass   


# entry point for running the script as an executable
if __name__ == "__main__":  # pragma: no cover (undocumented, little used executable entry point)
	if len(sys.argv) < 2:
		print("Usage: fileunzip <unzip> <file> or")
		print("					<unzipall> <path>")
		sys.exit()
	else:
		try:
			if sys.argv[1] == 'unzip':
				status = unzip(sys.argv[2], 1)
			elif sys.argv[1] == 'unzipall':
				status = unzipall(sys.argv[2])
		except Exception:
			print("caught %s: %s" % (sys.exc_info()[0], sys.exc_info()[1]))
			print("unable to perform unzip operation") 
