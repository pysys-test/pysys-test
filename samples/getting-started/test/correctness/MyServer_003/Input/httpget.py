# Trivial HTTP client for use in sample test. Support optional decompression of server response. 
# NB it'd be possible to perform these operations in the main PySys process too but using separate processes for 
# I/O-intensive operations allows for greater multi-threaded testing performance

import urllib.request, sys, gzip

url, acceptencoding, auth = sys.argv[1:]

request = urllib.request.Request(url)
if acceptencoding:
	request.add_header('Accept-encoding', acceptencoding)
assert auth == 'AuthNone', 'Support for testing other auth types is not yet implemented'

with urllib.request.urlopen(request) as r:
	body = r.read()
	assert r.headers.get('Content-encoding','') == acceptencoding, 'Got unexpected encoding: %r'%r.headers.get('Content-encoding')
	if r.headers.get('Content-encoding','') == 'gzip':
		body = gzip.decompress(body)

	print(body.decode('utf-8'))
