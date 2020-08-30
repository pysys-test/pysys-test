# Print out the process environment
#
import sys
import os.path

# entry point for running the script as an executable
if __name__ == "__main__":
	sys.stdout.write("Writing process environment\n")
	sys.stdout.flush()
	
	keys = list(os.environ.keys())
	keys.sort()
	
	for key in keys:
		sys.stdout.write("%s=%s\n" % (key, os.environ[key]))
		sys.stdout.flush()
	
	sys.stdout.write("Written process environment\n")
	sys.stdout.flush()
	
		
				