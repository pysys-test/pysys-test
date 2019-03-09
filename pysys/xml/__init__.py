#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2019 M.B. Grieve

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
