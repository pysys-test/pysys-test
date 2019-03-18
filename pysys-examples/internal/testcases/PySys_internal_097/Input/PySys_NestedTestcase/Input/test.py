import tempfile, os
print('TempDir=%s'%os.path.normpath(tempfile.gettempdir()))
print('Python environment: %s'%os.environ)
print('Python executed successfully')