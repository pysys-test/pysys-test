import os, sys
import pysys
from pysys.constants import IS_WINDOWS, FAILED
from pysys.utils.filecopy import filecopy
from pysys.xml.project import createProjectConfig

def runPySys(processowner, stdouterr, args, ignoreExitStatus=False, abortOnError=True, environs=None, projectfile=None, defaultproject=False, expectedExitStatus='==0', **kwargs):
	"""
	Executes pysys from within pysys. Used only by internal pysys testcases. 
	"""
	# for compatibility with some existing tests
	if isinstance(expectedExitStatus, int): expectedExitStatus = '==%d'%expectedExitStatus
	
	if sys.argv[0].endswith('pysys.py'):
		args = [os.path.abspath(sys.argv[0])]+args
	else:
		args = ['-m', 'pysys']+args

	# allow controlling lang from the parent e.g. via Travis, if not explicitly set
	if not IS_WINDOWS and 'LANG' not in (environs or {}) and 'LANG' in os.environ: 
		environs = dict(environs or {})
		environs['LANG'] = os.environ['LANG']
		if environs['LANG'] == 'C':
			environs['LANGUAGE'] = 'C'
			environs['LC_ALL'] = 'C'
			environs['PYTHONUTF8'] = '0'
			environs['PYTHONCOERCECLOCALE'] = '0'

	environs = processowner.createEnvirons(overrides=environs, command=sys.executable)
	
	if defaultproject:
		createProjectConfig(os.path.join(processowner.output, kwargs.get('workingDir', '.')))
	
	if projectfile:
		environs['PYSYS_PROJECTFILE'] = os.path.join(processowner.input, projectfile)
	else:
		# ensure there's a project file else it'll use the parent one and potentially compete to overwrite the junit reports etc
		if 'makeproject' not in args:
			assert os.path.exists(os.path.join(processowner.output, kwargs.get('workingDir', processowner.output), 'pysysproject.xml')) or os.path.exists(processowner.output+'/pysysproject.xml')
	
	# since we might be running this from not an installation
	environs['PYTHONPATH'] = os.pathsep.join(sys.path)

	result = processowner.startPython(
			arguments = args,
			environs = environs,
			expectedExitStatus=expectedExitStatus,
			ignoreExitStatus=ignoreExitStatus, abortOnError=abortOnError, 
			stdout=stdouterr+'.out', stderr=stdouterr+'.err', 
			displayName='pysys %s'%stdouterr, 
			**kwargs)
	return result

class PySysTestPlugin:
	def setup(self, testObj):
		self.testObj = testObj
	
	def pysys(self, stdouterr, *args, **kwargs):
		runPySys(self.testObj, stdouterr, *args, **kwargs)
	