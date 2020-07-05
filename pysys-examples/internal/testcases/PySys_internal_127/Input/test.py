import sys, time
sys.stdout.write('Process stdout output\nUmmmmm\nis here')
sys.stderr.write('Process stderr output\nis here')
if sys.argv[-1] == 'block':
	sys.stdout.write('\nBlocking now')
	sys.stdout.flush()
	sys.stderr.flush()
	time.sleep(1000)
sys.exit(1)