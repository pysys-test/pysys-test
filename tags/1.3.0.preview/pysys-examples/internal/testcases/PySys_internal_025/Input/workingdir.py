# Print out the process environment
#
import os, os.path, sys, string

# entry point for running the script as an executable
if __name__ == "__main__":
	sys.stderr.write("Current working directory is %s\n" % os.getcwd().replace("\\", "/"))
	sys.stderr.flush()
	
	sys.stdout.write("Writing contents of working directory\n")
	for file in os.listdir(os.getcwd()):
		sys.stdout.write("   %s\n" % file)
	sys.stdout.write("Written contents of working directory\n")
	sys.stdout.flush()
	
		
				