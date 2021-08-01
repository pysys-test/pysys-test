# Trivial HTTP client for use in sample test
# NB it'd be possible to perform these operations in the main PySys process too but using separate processes for 
# I/O intensive operations allows for greater multi-threaded testing performance

import urllib.request, sys
with urllib.request.urlopen(sys.argv[1]) as r:
	print(r.read().decode('utf-8'))
