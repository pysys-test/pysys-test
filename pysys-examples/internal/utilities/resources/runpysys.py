def runPySys(processowner, stdouterr, args, ignoreExitStatus=False, abortOnError=True, environs=None, projectfile=None, **kwargs):
	"""
	Executes pysys from within pysys. Used only by internal pysys testcases. 
	"""
	import os, sys
	from pysys.constants import IS_WINDOWS
	if sys.argv[0].endswith('pysys.py'):
		args = [os.path.abspath(sys.argv[0])]+args
	else:
		args = ['-m', 'pysys']+args

	environs = processowner.createEnvirons(overrides=environs, command=sys.executable)
	
	if projectfile:
		environs['PYSYS_PROJECTFILE'] = os.path.join(processowner.input, projectfile)
	
	# allow controlling lang from the parent e.g. via Travis
	if not IS_WINDOWS: 
		environs['LANG'] = os.getenv('LANG','en_US.UTF-8')
		if environs['LANG'] == 'C':
			environs['LANGUAGE'] = 'C'
			environs['LC_ALL'] = 'C'
			environs['PYTHONUTF8'] = '0'
			environs['PYTHONCOERCECLOCALE'] = '0'
			
	# since we might be running this from not an installation
	environs['PYTHONPATH'] = os.pathsep.join(sys.path)

	try: 
		import coverage
	except ImportError: pass
	else:
		# if this python has the "coverage" package installed, use it to generate 
		# output for child processes; otherwise we'd only get coverage for things 
		# that can be tested using the top-level pysys invocation
		args = ['-m', 'coverage', 'run', '--parallel-mode']+args
	try:
		return processowner.startProcess(command=sys.executable,
			arguments = args,
			environs = environs,
			ignoreExitStatus=ignoreExitStatus, abortOnError=abortOnError, 
			stdout=stdouterr+'.out', stderr=stdouterr+'.err', 
			displayName='pysys %s'%stdouterr, 
			**kwargs)
	finally: # in case there was any error printed to stderr
		processowner.logFileContents(stdouterr+'.err')
