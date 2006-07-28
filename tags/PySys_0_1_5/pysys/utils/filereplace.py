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

import os.path, sys, string

from pysys.exceptions import *;


def replace(input, output, dict={}, marker='$'):
	if not os.path.exists(input):
		raise FileNotFoundException, "unable to find file %s" % (os.path.basename(input))
	else:
		fi = open(input, 'r')
		fo = open(output, 'w')
		for line in fi.readlines():
			for key in dict.keys():
				line = string.replace(line, '%s%s%s'%(marker, key, marker), "%s" % (dict[key]))
			fo.write(line)
		fi.close()
		fo.close()

	
