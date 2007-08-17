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

import os, os.path, stat, sys, string, glob, gzip
from pysys.constants import *;
from pysys.exceptions import *;


def unzipall(path, binary=FALSE):
	if not os.path.exists(path):
		raise FileNotFoundException, "%s path does not exist" % (os.path.basename(path))

	for file in glob.glob('%s/*.gz'%(path)):
		unzip(file, 1, binary)



def unzip(zfilename, replace=FALSE, binary=FALSE):
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
