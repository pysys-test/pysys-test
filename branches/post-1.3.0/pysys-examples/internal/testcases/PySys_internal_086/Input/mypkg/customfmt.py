from pysys.utils.logutils import ColorLogFormatter
from pysys import stdoutHandler
import logging, os, sys, locale

# purely a hack to allow us to patch getpreferredencoding() before the coloring initializes (and before runner starts opening run.log files etc)

if os.getenv('LANG','') and 'win' in sys.platform:
	# bizarely Python has no cross-platform way to customize the preferred encoding via env vars, so have to monkey-patch locale module to get consistent testing on Windows
	encodingoverride = os.getenv('LANG','').split('.')[-1]
	def customized_getpreferredencoding(do_setlocale=True): 
		return encodingoverride
	locale.getpreferredencoding = customized_getpreferredencoding 
	sys.stdout.write('HACKED preferred encoding to: %s\n'%locale.getpreferredencoding())
	
	# if coloring is not enable we need to explicitly recreate the stream wrapper with the new encoding
	stdoutHandler._updateUnderlyingStream()

class CustomFormatter(ColorLogFormatter):
	pass
