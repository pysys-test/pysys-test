import time, sys
t = time.time()
val1, val2 = 0, 1
iterations = 0
# For demonstration purposes we will run for a fixed time period, 
# just to ensure we generate sensible results regardless of the hardware 
# we're running on
while time.time() < t+1:
	batchsize = 10000
	for x in range(batchsize): # do the calculations in batches to avoid calling .time() too often which would end up skewing the results
		val1, val2 = val2, val1+val2
	iterations += batchsize
sys.stdout.write('completed %d calculations in %f seconds\n'%(iterations, time.time()-t))
