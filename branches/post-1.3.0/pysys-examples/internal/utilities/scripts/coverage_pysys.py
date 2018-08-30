# Read lines in from stdin and echo them out with 
# the line number prepended
#
from __future__ import print_function
import time, sys, os.path

TESTS_DIR = os.path.normpath(os.path.dirname(__file__)+'/../../..')
def getCoverageFiles():
	assert TESTS_DIR.endswith('pysys-examples'), TESTS_DIR
	cov = []
	for (dirpath, dirnames, filenames) in os.walk(TESTS_DIR):
		for f in filenames:
			if f.startswith('.coverage'): cov.append(os.path.join(dirpath, f))
	return cov

def main(args):
	if 'report' in args:
		files = getCoverageFiles()
		if not files: raise Exception('No coverage files found')
		print('\n'.join(files))
		print('found %d coverage file(s) in %s'%(len(files), TESTS_DIR))
		import coverage
		if os.path.exists('combined-pysys-coverage'): os.remove('combined-pysys-coverage')
		c = coverage.Coverage('combined-pysys-coverage')
		# nb: combine automatically deletes all the files (!)
		c.combine(files)
		# ... so it's a good idea to save a new combined file so we're not left with nothing
		c.save() 
		include = ['*/pysys.py', '*/pysys/*']
		print('generating html report')
		c.html_report(directory='coverage-pysys-html', 
			title='PySys coverage report',
			include=include
			)
		print('wrote HTML report to: %s'%os.path.abspath('coverage-pysys-html'))
		c.xml_report(outfile='coverage-pysys.xml', include=include)
		c.report(file=sys.stdout, include=include)
	else:
		print('This tool is for producing a code coverage report for the PySys project from a source distribution')
		print('The "coverage" package must be installed before this can be used')
		print()
		print('Usage for this tool:')
		print('   > coverage_pysys.py report   -- generate a coverage HTML report')
		print('')
		print('To generate a coverage report, run:')
		print('   > cd pysys-examples')
		print('   > python -m coverage run ../pysys-dist/scripts/pysys.py run -n0'.replace('/',os.sep))
		print('   > internal/utilities/scripts/coverage_pysys.py report'.replace('/',os.sep))
		
if __name__ == "__main__":
	main(sys.argv[1:])
