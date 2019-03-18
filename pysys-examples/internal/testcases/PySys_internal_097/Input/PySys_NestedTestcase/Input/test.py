import tempfile, os
print('TempDir=%s'%os.path.normpath(tempfile.gettempdir()))
print('Python environment: %s.'%', '.join([k for k in os.environ.keys() if not k.startswith('LC_')]))
print('Python executed successfully')