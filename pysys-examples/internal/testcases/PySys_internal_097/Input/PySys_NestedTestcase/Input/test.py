import tempfile, os
print('TempDir=%s'%os.path.normpath(tempfile.gettempdir()))
print('Python environment: %s.'%', '.join([k for k in os.environ.keys() 
	# some OSes e.g. mac define some internal ones like __PYVENV_LAUNCHER__ etc, and others some encoding-related ones
	if not k.startswith('LC_') and not k.startswith('__')]))
print('Python executed successfully')