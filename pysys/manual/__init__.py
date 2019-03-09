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
Contains modules for the Manual Test User Interface. 

The Manual Test UI is used to detail test steps to be performed via manual intervention, 
i.e. when a series of test steps cannot be automated through the execution of an 
external process etc. The UI displays the test steps through loading of an XML file 
detailing the required information to be presented to the user, and allows for easy 
navigation through the steps, and for passing / failing steps that require explicit 
verification. 

Starting of the Manual Test UI is through L{pysys.basetest.BaseTest.startManualTester}, so 
it can be performed alongside automated steps, e.g. to setup the test prior to the 
manual steps being performed, or to perform as much automation as possible so as to limit the 
time required for manual intervention. This approach utilises the automated regression facilities 
of the PySys framework, provides autdit trail logging of manual tests as for automated tests, and 
makes it easy at a future date to remove the manual steps when automation is possible i.e. through 
scriptable record and playback test tools for user interface testing etc.   

"""
__all__ = [ "ui",
			"xmlhandler" ]




