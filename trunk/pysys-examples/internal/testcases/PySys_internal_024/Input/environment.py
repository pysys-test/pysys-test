# Print out the process environment
#
import time, sys, os.path

# entry point for running the script as an executable
if __name__ == "__main__":
	sys.stdout.write("Writing process environment\n")
	sys.stdout.flush()
	for env in os.environ:
		sys.stdout.write("%-20s: %s\n" % (env, os.environ[env]))
		sys.stdout.flush()
	
	sys.stdout.write("Written process environment\n")
	sys.stdout.flush()
	
		
				