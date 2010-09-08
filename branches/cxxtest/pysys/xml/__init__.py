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
"""
Contains classes for parsing and abstracting XML data files used by the PySys framework. 

Currently the PySys framework uses two different types of XML format data files for 
detailing information about a particular project, and a particular test within that 
project; these are the PySys project file and test descriptors respectively. Manual 
testcases also use an XML format file to detail the manual steps that should be presented
to a user via the Manual Test User Interface, and also whether the steps require validation
etc. 

"""

__all__ = [ "descriptor",
			"project",
			"manual" ]
