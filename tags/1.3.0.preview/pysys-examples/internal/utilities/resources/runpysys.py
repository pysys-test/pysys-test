def runPySys(processowner, stdouterr, args, ignoreExitStatus=False, abortOnError=True, environs=None, **kwargs):
	"""
	Executes pysys from within pysys. Used only by internal pysys testcases. 
	"""
	import os, sys
	args = [os.path.abspath([a for a in sys.argv if a.endswith('pysys.py')][0])] + args
	env = dict(environs or {})
	for k in os.environ: 
		if not k.startswith('PYSYS_'): env[k] = os.environ[k]
	pypath = os.path.dirname(sys.executable)
	if not env.get('PATH','').startswith(pypath+os.pathsep):
		# whatever python we're using, make sure it's on path, otherwise in some cases child pythons don't have sys.executable set
		env['PATH'] = pypath+os.pathsep+env.get('PATH','')
			
	try: 
		import coverage
	except ImportError: pass
	else:
		# if this python has the "coverage" package installed, use it to generate 
		# output for child processes; otherwise we'd only get coverage for things 
		# that can be tested using the top-level pysys invocation
		args = ['-m', 'coverage', 'run', '--parallel-mode']+args
		
	return processowner.startProcess(command=sys.executable,
		arguments = args,
		environs = env, ignoreExitStatus=ignoreExitStatus, abortOnError=abortOnError, 
		stdout=stdouterr+'.out', stderr=stdouterr+'.err', 
		displayName='pysys %s'%stdouterr, 
		**kwargs)
