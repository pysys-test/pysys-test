import os.path
from pysys.constants import *

# set the modules to import when imported the pysys.process package
__all__ = [ "helper",
			"monitor" ]

# add to the __path__ to import the platform specific helper class
dirname = __path__[0]
if PLATFORM in [ "sunos", "linux" ]:
	__path__.append(os.path.join(dirname, "plat-unix"))
else:
	__path__.append(os.path.join(dirname, "plat-win32"))



