# Read lines in from stdin and echo them out with 
# the line number prepended
#
import time, sys, os.path

count = 0
for line in sys.stdin:
	sys.stdout.write("Line %s: Read in %r\n" % (count, line))
	sys.stdout.flush()
	count+=1
sys.stdout.write('EOF\n')
sys.stdout.flush()
