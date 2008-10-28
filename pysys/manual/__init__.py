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




