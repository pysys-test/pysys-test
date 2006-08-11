"""PySys System Test Framework.

"""

import sys, logging
logging._levelNames[50] = 'CRIT'

__author__  = "Moray Grieve"
"""The author of PySys."""

__author_email__ = "moraygrieve@users.sourceforge.net"
"""The author's email address."""

__status__  = "alpha"
"""The status of this release."""

__version__ = "0.1.7"
"""The version of this release."""

__date__    = "11 August 2006"
"""The date of this release."""

__all__     = [ "constants",
                "exceptions",
                "baserunner",
                "basetest",
                "launcher",
                "manual",
                "process",
                "utils",
                "xml"]
"""The submodules of PySys."""

rootLogger = logging.getLogger('pysys')
"""The root logger for all logging within PySys."""

rootLogger.setLevel(logging.INFO)
