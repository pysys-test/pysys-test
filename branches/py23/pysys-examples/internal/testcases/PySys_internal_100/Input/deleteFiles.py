import sys, os

NUM_FILES = sys.argv[1]
sys.stdout.write("Deleting %s files...\n" % NUM_FILES)
for i in range(1, int(NUM_FILES)+1):
    os.remove(os.path.join(sys.argv[2], "%d.txt" % i))
sys.stdout.write("Done\n")
