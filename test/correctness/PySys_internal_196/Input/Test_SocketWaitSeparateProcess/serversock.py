import socketserver, time, sys

class MyTCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        print("Server got client connection, now blocking forever")
        sys.stdout.flush()
        time.sleep(60*2*1000)

with socketserver.TCPServer(('localhost', int(sys.argv[1])), MyTCPHandler) as server:
	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	print("Server started on port %s"%sys.argv[1])
	sys.stdout.flush()
	server.serve_forever()
