# Print out a loop count every one second, and 
# exit with a pre-defined exit status
#
import time, sys, os.path

def run(loops, status):
	count = 0
	while 1:
		sys.stdout.write("Count is %d\n" % count)
		sys.stdout.flush()
		count = count + 1
		if count >= loops: break
		time.sleep(0.5)
	sys.exit(status)

# entry point for running the script as an executable
if __name__ == "__main__":
	if len(sys.argv) < 2:
		sys.stdout.write("Usage: %s <count> <exit status>\n" % os.path.basename(sys.argv[0]))
	else:
		sys.stderr.write("Process id of test executable is %d" % os.getpid())
		sys.stderr.flush()
		run(int(sys.argv[1]), int(sys.argv[2]))
