# Trivial example of a tool to measure HTTP performance. 1This is just for illustration - in a real test of an HTTP 
# server you'd probably want to use something rather more sophisticated. 

# NB it'd be possible to perform these operations in the main PySys process too but using separate processes for 
# I/O-intensive operations allows for greater multi-threaded testing performance

import urllib.request, sys, time, json, gzip

url, plannedIterations, acceptencoding = sys.argv[1:]
plannedIterations = int(plannedIterations)

startTime = time.time()
responses = 0

# Record a sample of latency values - aiming for 100 samples (i.e. not too often, to avoid disrupting throughput).
latencySamplingPeriod = max(1, plannedIterations // 100)

def performRequestResponse():
	request = urllib.request.Request(url)
	if acceptencoding:
		request.add_header('Accept-encoding', acceptencoding)
	with urllib.request.urlopen(request) as r:
		result = r.read()
		assert len(result)>0
		return result
# before we start the perf test check we're getting valid results
assert json.loads(gzip.decompress(performRequestResponse()))

# In case the specified number of iterations runs too quickly on this machine to get stable results, 
# add a time-based retry loop, e.g. ensuring we spend at least 2 seconds. In a real test this would be longer.
while responses==0 or time.time()-startTime < 2:
	for i in range(plannedIterations):
		if i % 1000 == 0: 
			print(f'Progress: iteration={i:,} (={100.0*i/plannedIterations:0.1f}%)')
			sys.stdout.flush()

		if (i % latencySamplingPeriod == 0): latencyStartTime = time.time()
		
		performRequestResponse()

		if (i % latencySamplingPeriod == 0): print(f'Response latency sample: {time.time()-latencyStartTime} seconds')
		responses += 1
	
print(f'Completed {responses:,} response iterations in {time.time()-startTime} seconds')
