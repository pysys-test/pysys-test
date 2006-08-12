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


import sys, os

def install():
	pass


def printUsage():
	print "\nUsage: %s [option]" % os.path.basename(sys.argv[0])
	print "    where option is one of;"
	print "       -install         perform the post install steps"
	print "       -remove          perform the post uninstall steps"
	print ""
	sys.exit()


if __name__=='__main__':
    if len(sys.argv)==1:
    	printUsage()
        sys.exit(1)

    arg_index = 1
    while arg_index < len(sys.argv):
        arg = sys.argv[arg_index]

        if arg == "-install":
            install()
        elif arg == "-remove":
            pass
        else:
            print "Unknown option:", arg
            sys.exit(0)
        arg_index += 1
