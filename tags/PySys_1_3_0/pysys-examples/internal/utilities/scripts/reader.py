# Read lines in from stdin and echo them out with 
# the line number prepended
#
import time, sys, os.path

def run(loops):
	count = 0
	while 1:
		line = sys.stdin.readline()
		sys.stdout.write("Line (%s): Read in %s" % (count, line))
		sys.stdout.flush()
		count = count + 1
		if count >= loops: break
		time.sleep(0.5)

# entry point for running the script as an executable
if __name__ == "__main__":
	if len(sys.argv) < 1:
		sys.stdout.write("Usage: %s <count>\n" % os.path.basename(sys.argv[0]))
	else:
		run(int(sys.argv[1]))
