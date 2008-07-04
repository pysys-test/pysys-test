"""PySys System Test Framework.

PySys has been designed to provide a generic extensible framework for the organisation and execution of system level testcases. 
It provides a clear model of what a testcases is, how it is structured on disk, how it is executed and validated, and how the 
outcome is reported for test auditing purposes. 

Testcases are instances of a base test class (L{pysys.basetest.BaseTest}) which provides core functionality for cross platform 
process management and manipulation; in this manner an application under test (AUT) can be started and manipulated directly 
within the testcase. The base test class additionally provides a set of standard validation techniques based predominantly 
on regular expression matching within text files (e.g. stdout, logfile of the AUT etc). Testcases are executed through a base 
runner (L{pysys.baserunner.BaseRunner}) which provides the mechanism to control testcase flow and auditing. In both cases the 
base test and runner classes have been designed to be extended for a particular AUT, e.g. to allow a higher level of abstraction 
of AUT manipulation, tear up and tear down prior to executing a set of testcases etc. 

PySys allows automated regression testcases to be built rapidly. Where an AUT cannot be tested in an automated fashion, testcases 
can be written to make use of a manual test user interface application (L{pysys.manual.ui.ManualTester}) which allows the steps 
required to execute the test to be presented to a tester in a concise and navigable manner. The tight integration of both manual 
and automated testcases provides a single framework for all test organisation requirements. 

"""

import sys, logging
logging._levelNames[50] = 'CRIT'
logging._levelNames[30] = 'WARN'

__author__  = "Moray Grieve"
"""The author of PySys."""

__author_email__ = "moraygrieve@users.sourceforge.net"
"""The author's email address."""

__status__  = "beta"
"""The status of this release."""

__version__ = "0.5.2"
"""The version of this release."""

__date__    = "3 July 2008"
"""The date of this release."""

__all__     = [ "constants",
                "exceptions",
                "baserunner",
                "basetest",
                "interfaces",
                "launcher",
                "manual",
                "process",
                "utils",
                "writer",
                "xml"]
"""The submodules of PySys."""

rootLogger = logging.getLogger('pysys')
"""The root logger for all logging within PySys."""

rootLogger.setLevel(logging.INFO)
