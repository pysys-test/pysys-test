# Trivial HTTP client for use in sample test. Support optional decompression of server response. 
# NB it'd be possible to perform these operations in the main PySys process too but using separate processes for 
# I/O-intensive operations allows for greater multi-threaded testing performance

import urllib.request, sys, gzip

url, acceptencoding, auth = sys.argv[1:]

request = urllib.request.Request(url)
if acceptencoding != 'None':
	request.add_header('Accept-encoding', acceptencoding)
assert auth == 'None', 'Support for testing other auth types is not yet implemented ("%s")'%auth

with urllib.request.urlopen(request) as r:
	body = r.read()
	assert r.headers.get('Content-encoding','None') == acceptencoding, 'Got unexpected encoding %r, expected %r'%(r.headers.get('Content-encoding'), acceptencoding)
	if r.headers.get('Content-encoding','') == 'gzip':
		body = gzip.decompress(body)

	print(body.decode('utf-8'))
