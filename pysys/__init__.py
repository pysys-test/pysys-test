import sys, logging

__author__  = "Moray Grieve (moray.grieve@ntlworld.com)"
__status__  = "beta"
__version__ = "0.1"
__date__    = "07 April 2006"
__all__     = [ "constants",
                "exceptions",
                "baserunner",
                "basetest",
                "launcher",
                "maker",
                "manual",
                "process",
                "utils",
                "xml"]

# setup the logging for the pysys package
logging._levelNames[50] = 'CRIT'
rootLogger = logging.getLogger('pysys')
rootLogger.setLevel(logging.INFO)
