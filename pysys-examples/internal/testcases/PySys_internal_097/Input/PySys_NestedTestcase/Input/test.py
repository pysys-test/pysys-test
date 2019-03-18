import tempfile, os
print('TempDir=%s'%os.path.normpath(tempfile.gettempdir()))
print('Python environment: %s.'%', '.join(os.environ.keys()))
print('Python executed successfully')