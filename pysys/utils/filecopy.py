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
# dealings in the software.

import sys

def __copyfileobj(fsrc, fdst, length=16*1024):
   while 1:
      buf = fsrc.read(length)
      if not buf:
         break
      fdst.write(buf)


def filecopy(src, dst):
   fsrc = None
   fdst = None
   try:
      fsrc = open(src, 'rb')
      fdst = open(dst, 'wb')
      __copyfileobj(fsrc, fdst)
   finally:
      if fdst:
         fdst.close()
      if fsrc:
         fsrc.close()


# entry point for running the script as an executable
if __name__ == "__main__":
   if len(sys.argv) < 2:
      print "Usage: fileunzip <src> <dst>"
      sys.exit()
   else:
      filecopy(sys.argv[1], sys.argv[2])
      

