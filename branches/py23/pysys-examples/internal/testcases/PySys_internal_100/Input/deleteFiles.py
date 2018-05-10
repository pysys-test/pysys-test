import sys, os

NUM_FILES = sys.argv[1]
print("Deleting %s files..." % NUM_FILES)
for i in range(1, int(NUM_FILES)+1):
    os.remove(os.path.join(sys.argv[2], "%d.txt" % i))
print("Done")
