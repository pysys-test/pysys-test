#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2016  M.B.Grieve

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

# Contact: moraygrieve@users.sourceforge.net

import os, os.path, stat, sys, string, glob, gzip

from pysys.constants import *
from pysys.exceptions import *


def unzipall(path, binary=False):
	"""Unzip all .gz files in a given directory.
	
	@param path: The full path to the directory containing the archive files
	@param binary: Boolean flag to indicate if the unzipped files should be written as binary 
	@raises FileNotFoundException: Raised if the directory path does not exist
	
	"""
	if not os.path.exists(path):
		raise FileNotFoundException, "%s path does not exist" % (os.path.basename(path))

	for file in glob.glob('%s/*.gz'%(path)):
		unzip(file, 1, binary)



def unzip(zfilename, replace=False, binary=False):
	"""Unzip a .gz archive and write the contents to disk.
	
	The method will unpack a file of the form C{file.data.gz} to C{file.data}, removing the 
	archive file in the process if the replace input parameter is set to true. By default the 
	unpacked archive is written as text data, unless the binary input parameter is set to true,
	in which case the unpacked file is written as binary.
	
	@param zfilename: The full path to the archive file
	@param replace: Boolean flag to indicate if the archive file should be removed after unpacking
	@param binary: Boolean flag to indicate if the unzipped file should be written as binary
	@raises FileNotFoundException: Raised if the archive file does not exist
	@raises IncorrectFileTypeEception: Raised if the archive file does not have a .gz extension
	
	"""
	if not os.path.exists(zfilename):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(zfilename))

	tokens	= string.split(zfilename, '.')
	if tokens[len(tokens)-1] != 'gz':
		raise IncorrectFileTypeException, "file does not have a .gz extension"
	
	uzfilename = ''
	for i in range(len(tokens)-1):
		uzfilename = uzfilename + tokens[i]
		if i != len(tokens)-2:
			uzfilename = uzfilename + '.'

	zfile = gzip.GzipFile(zfilename, 'rb', 9)
	if binary:
		uzfile = open(uzfilename, 'wb')
	else:
		uzfile = open(uzfilename, 'w')
	buffer = zfile.read()
	uzfile.write(buffer)
	zfile.close()	 
	uzfile.close()

	if replace:
		try:
			os.remove(zfilename)
		except OSError:
			pass   


# entry point for running the script as an executable
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "Usage: fileunzip <unzip> <file> or"
		print "					<unzipall> <path>"
		sys.exit()
	else:
		try:
			if sys.argv[1] == 'unzip':
				status = unzip(sys.argv[2], 1)
			elif sys.argv[1] == 'unzipall':
				status = unzipall(sys.argv[2])
		except:
			print "caught %s: %s" % (sys.exc_info()[0], sys.exc_info()[1])
			print "unable to perform unzip operation" 
