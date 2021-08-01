import time, logging, sys

logging.basicConfig(format='%(asctime)-15s %(levelname)6s %(message)s', stream=sys.stdout)
log = logging.getLogger()

log.info('Server is starting...')

# Just to demonstrate the point
if True:
	log.error('Cannot bind TCP listening port on one or more of the requested network interfaces')
else:
	log.info('Started MyServer on port 12345')

time.sleep(100)
