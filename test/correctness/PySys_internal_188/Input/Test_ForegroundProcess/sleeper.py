import time, sys
while True:
	try:
		print('Sleeping')
		sys.stdout.flush()
		time.sleep(120)
	except BaseException as ex:
		print('Ignoring exception: %r'%ex)
		sys.stdout.flush()
	finally:
		print('... finally block')
		sys.stdout.flush()
