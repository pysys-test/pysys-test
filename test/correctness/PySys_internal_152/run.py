import pysys
from pysys.constants import *
from pysys.basetest import BaseTest

class PySysTest(BaseTest):

	def execute(self):
		pass
		
	def validate(self):	

		sampledir = self.project.testRootDir+'/../samples'
		
		pythonVersionForCI = "3.8"
		pythonVersionForMin = "3.6"
		
		pysysVersion = pysys.__version__
		if 'dev' in pysysVersion: pysysVersion = pysysVersion[:pysysVersion.find('.dev')]
		#pysysVersion = '1.6.1' # temporarily force it to the current released version

		badfiles = []

		for root, dirs, files in os.walk(pysys.utils.fileutils.toLongPathSafe(sampledir)):
			root = pysys.utils.fileutils.fromLongPathSafe(root)
			for d in list(dirs): # python cache files and outputs
				if d.startswith('__'): dirs.remove(d)
			if 'Output' in dirs: dirs.remove('Output')
			for f in files:
				if f.endswith('.pyc'): continue
			
				failuresBefore = len([o for o in self.outcome if o.isFailure()])
				p = root+os.sep+f
				# ensure no non-ASCII characters - would throw if there are any non-ASCII chars
				self.assertGrep(p, 'NON_ASCII_CHECK', contains=False, encoding='ascii')
				 
				if f.endswith('.xml') and f not in ['input.xml']:
					self.assertGrep(p, '^  .*', contains=False) # check indentation is with tabs not spaces
					self.assertGrep(p, '^<[?]xml version="1.0" encoding="utf-8"[?]>$') # proper XML header with encoding explicitly specified
				if f == 'pysystest.xml':
					self.assertGrep(p, '^<pysystest type="[^"]+">$')
				if f == 'pysysproject.xml':
					self.assertThatGrep(p, '<requires-python>(.*)</requires-python>', expected=pythonVersionForMin)	
					self.assertThatGrep(p, '<requires-pysys>(.*)</requires-pysys>', 'value == pysysVersion', pysysVersion=pysysVersion)
				
				if f == 'pysys-test.yml': # GitHub Actions workflow
					self.assertThatGrep(p, ' pip install pysys==(.*)', 'value == pysysVersion', pysysVersion=pysysVersion)
					self.assertThatGrep(p, ' python-version: (.*)', 'value == pythonVersionForCI', pythonVersionForCI=pythonVersionForCI)

				if f == 'run.py':
					self.assertGrep(p, 'import pysys') # new-style test not an old one we copied from somewhere
				
				if failuresBefore != len([o for o in self.outcome if o.isFailure()]): badfiles.append(p)

			if files: self.log.info('')

		if badfiles:
			self.log.info('These files need attention: \n%s', '\n'.join(badfiles))