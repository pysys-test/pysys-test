#!/usr/bin/env python3

import sys
import os
import time
import argparse
import http.server
import socketserver
import json
import logging
import threading
import datetime
import socket
import gzip

__version__ = '1.0.0'

logging.basicConfig(format='%(asctime)-15s %(levelname)6s %(message)s', stream=sys.stdout)
log = logging.getLogger()

os.chdir(os.path.dirname(__file__))
try:

	parser = argparse.ArgumentParser(description='MyServer - a trivial HTTP server used to illustrate how to test a server with PySys.')
	parser.add_argument('--port', dest='port', type=int, help='The port to listen on')
	parser.add_argument('--loglevel', dest='loglevel', help='The log level e.g. INFO/DEBUG', default='INFO')
	parser.add_argument('--configfile', dest='configfile', help='The JSON configuration file for this server')
	args = parser.parse_args()

	if args.configfile:
		with open(args.configfile) as f:
			config = json.load(f)
		assert not args.port, 'Cannot specify port twice'
		args.port = config['port']

	assert args.port > 0, 'Invalid port number specified: %s'%args.port

	log.setLevel(getattr(logging, args.loglevel.upper()))

	class MyHandler(http.server.SimpleHTTPRequestHandler):
		def log_message(self, format, *args):
			log.info(format, *args)

		def do_GET(self):
			t = time.time()
			if self.path == '/shutdown':
				log.info('Clean shutdown requested')
				self.send_response(200)
				self.end_headers()
				self.flush_headers()
				sys.exit(0)

			elif self.path == '/otherRequest':
				raise Exception('Not implemented yet')

			elif self.path == '/sensorValues':
				# dynamically generate some data
				body = json.dumps({
					'sensorId':'ABC1234',
					'timestamp':'%s.%03d'%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.datetime.now().microsecond/1000),
					'collectionHost':socket.gethostname(),
					'measurements':[
						123.4,
						670,
						10/3.0,
						None,
						123.4,
					], 
					'measurementTimeSpanSecs': 2.5,
					'dataPaths':r'c:\devicedata*\sensor.json',
				}).encode('utf-8')
				
				self.send_response(200)
				if self.headers.get('Accept-encoding', None) == 'gzip':
					body = gzip.compress(body)
					self.send_header("Content-length", str(len(body)))
					self.send_header("Content-Encoding", "gzip")
				
				self.end_headers()
				self.wfile.write(body)
			else:
				super().do_GET()

	httpd = socketserver.TCPServer(("127.0.0.1", args.port), MyHandler)

	log.debug('Initializing server with args: %s', sys.argv[1:])
	log.info("Started MyServer v%s on port %d", __version__, args.port)
	httpd.serve_forever()
except Exception as ex:
	log.exception('Server failed: %s', ex, exc_info=True)
	sys.exit(123)
