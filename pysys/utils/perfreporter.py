#!/usr/bin/env python
# PySys System Test Framework, Copyright (C) 2006-2021 M.B. Grieve

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

"""
Performance number reporting classes, used by `pysys.basetest.BaseTest.reportPerformanceResult`. 

The `CSVPerformanceReporter` can be used as-is or subclassed for alternative output formats. 
"""

import collections, threading, time, math, sys, os

if __name__ == "__main__":
	sys.path.append(os.path.dirname( __file__)+'/../..')

from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *

class PerformanceUnit(object):
	"""Class which identifies the unit in which a performance result is measured.
	
	Every unit encodes whether big numbers are better or worse (which can be used 
	to calculate the improvement or regression when results are compared), e.g. 
	better for throughput numbers, worse for time taken or latency numbers. 
	
	For consistency, we recommend using the pre-defined units where possible. 
	For throughput numbers or rates, that means using PER_SECOND. For latency 
	measurements that means using SECONDS if long time periods of several 
	seconds are expected, or NANO_SECONDS (=10**-9 seconds) if sub-second 
	time periods are expected (since humans generally find numbers such as 
	1,234,000 ns easier to skim-read and compare than fractional numbers like 
	0.001234).

	"""
	def __init__(self, name, biggerIsBetter):
		assert biggerIsBetter in [False, True], biggerIsBetter
		self.name = name.strip()
		assert self.name
		self.biggerIsBetter = biggerIsBetter

	def __str__(self):
		return self.name

PerformanceUnit.SECONDS = PerformanceUnit('s', False)
PerformanceUnit.NANO_SECONDS = PerformanceUnit('ns', False) # 10**-9 seconds
PerformanceUnit.PER_SECOND = PerformanceUnit('/s', True)

class CSVPerformanceReporter(object):
	"""Class for receiving performance results and writing them to a file for later analysis.
	
	Each performance result consists of a value, a result key (which must 
	be unique across all test cases and modes, and also stable across different 
	runs), and a unit (which also encodes whether bigger values are better or worse). 
	Each test can report any number of performance results. 
	
	There is usually a single shared instance of this class per invocation of PySys. 
	It is possible to customize the way performance results are recorded by 
	providing a subclass and specifying it in the project performancereporter 
	element, for example to write data to an XML or JSON file instead of CSV. 
	Performance reporter implementations are required to be thread-safe. 
	
	The standard CSV performance reporter implementation writes to a UTF-8 file of 
	comma-separated values that is both machine and human readable and 
	easy to view and use in any spreadsheet program, and after the columns containing 
	the information for each result, contains comma-separated metadata containing 
	key=value information about the entire run (e.g. hostname, date/time, etc), 
	and (optionally) associated with each individual test result (e.g. test mode etc). 
	The per-run and per-result metadata is not arranged in columns since the structure 
	differs from row to row.

	After tests have run, the summary file is published with category "CSVPerformanceReport" 
	using the `pysys.writer.api.ArtifactPublisher` interface. 

	:param project: The project configuration instance.
	:param str summaryfile: The filename pattern used for the summary file(s). 
		If not specified explicitly, the summary file for the CSVPerformanceReporter can be configured 
		with the project property ``csvPerformanceReporterSummaryFile``. See `getRunSummaryFile()`. 
	
	:param str testoutdir: The output directory used for this test run 
		(equal to `runner.outsubdir`), an identifying string which often contains 
		the platform, or when there are multiple test runs on the same machine 
		may be used to distinguish between them. This is usually a relative path 
		but may be an absolute path. 
		
	:param runner: Pass this through to the superclass. 
	:param kwargs: Pass any additional keyword arguments through to the super class. 
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.csv'
	"""The default summary file if not overridden by the ``csvPerformanceReporterSummaryFile`` project property, or 
	the ``summaryfile=`` attribute. See `getRunSummaryFile()`. This is relative to the runner output+'/..' directory 
	(typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def __init__(self, project, summaryfile, testoutdir, runner, **kwargs):
		self.runner = runner
		assert self.runner is not None
		assert not kwargs, kwargs.keys() # **kwargs allows constructor to be extended in future if needed; give error if any unexpected args are passed
		
		self.testoutdir = os.path.basename(testoutdir)
		self.summaryfile = summaryfile
		self.project = project
		self.hostname = HOSTNAME.lower().split('.')[0]
		self.runStartTime = self.runner.startTime
		
		self._lock = threading.RLock()
		self.__previousResultKeys = {} # value = (testid, testobjhash, resultDetails)
		
		# anything listed here can be passed using just a string literal
		self.unitAliases = {
			's':PerformanceUnit.SECONDS, 
			'ns':PerformanceUnit.NANO_SECONDS, 
			'/s': PerformanceUnit.PER_SECOND
			}
		
		self.__summaryFilesWritten = set()
		
	def getRunDetails(self, testobj=None, **kwargs):
		"""Return an dictionary of information about this test run (e.g. hostname, start time, etc).
		
		Overriding this method is discouraged; customization of the run details should usually be performed by changing 
		the ``runner.runDetails`` dictionary from the `pysys.baserunner.BaseRunner.setup()` method. 

		:param testobj: the test case instance registering the value

		.. versionchanged:: 2.0 Added testobj parameter. 
		
		"""
		return collections.OrderedDict(self.runner.runDetails)
	
	def valueToDisplayString(self, value):
		"""Pretty-print an integer or float value to a moderate number of significant figures.

		The method additionally adds a "," grouping for large numbers.

		:param value: the value to be displayed

		"""
		if value > 1000:
			return '{0:,}'.format(int(value))
		else:
			valtostr = '%0.4g' % value
			if 'e' in valtostr: valtostr = '%f'%value
			return valtostr

	def getRunSummaryFile(self, testobj, **kwargs):
		"""Return the fully substituted location of the file to which summary performance results will be written.

		This may include the following substitutions: ``@OUTDIR@`` (=${outDirName}, the basename of the output directory for this run,
		e.g. "linux"), ``@HOSTNAME@``, ``@DATE@``, ``@TIME@``, and ``@TESTID@``. The default is given by `DEFAULT_SUMMARY_FILE`. 
		If the specified file does not exist it will be created; it is possible to use multiple summary files from the same
		run. The path will be resolved relative to the pysys project root directory unless an absolute path is specified.

		:param testobj: the test case instance registering the value

		"""
		summaryfile = self.summaryfile or getattr(self.project, 'csvPerformanceReporterSummaryFile', '') or self.DEFAULT_SUMMARY_FILE
		
		# properties are already expanded if set in project config, but needs doing explicitly in case default value was used
		summaryfile = self.runner.project.expandProperties(summaryfile)
		
		summaryfile = summaryfile\
			.replace('@OUTDIR@', os.path.basename(self.testoutdir)) \
			.replace('@HOSTNAME@', self.hostname) \
			.replace('@DATE@', time.strftime('%Y-%m-%d', time.localtime(self.runStartTime))) \
			.replace('@TIME@', time.strftime('%H.%M.%S', time.localtime(self.runStartTime))) \
			.replace('@TESTID@', testobj.descriptor.id)
		
		assert summaryfile, repr(getRunSummaryFile) # must not be empty
		summaryfile = os.path.normpath(os.path.join(self.runner.output+'/..', summaryfile))
		return summaryfile

	def getRunHeader(self, testobj=None, **kwargs):
		"""Return the header string to the CSV file."""
		
		try:
			runDetails = self.getRunDetails(testobj)
		except Exception: # for pre-2.0 signature
			runDetails = self.getRunDetails()
		
		return '# '+CSVPerformanceFile.toCSVLine(CSVPerformanceFile.COLUMNS+[CSVPerformanceFile.RUN_DETAILS, runDetails])+'\n'

	def cleanup(self):
		"""Called when PySys has finished executing tests."""
		with self._lock:
			if self.runner is not None and self.__summaryFilesWritten:
				for p in sorted(list(self.__summaryFilesWritten)):
					self.runner.publishArtifact(p, 'CSVPerformanceReport')

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		"""Report a performance result, with an associated unique key that identifies it.

		:param testobj: the test case instance registering the value
		:param value: the value to be reported. This may be an int, float, or a character (unicode) string. 
		:param resultKey: a unique string that fully identifies what was measured
		:param unit: identifies the unit the value is measured in
		:param toleranceStdDevs: indicates how many standard deviations away from the mean for a regression
		:param resultDetails:  A dictionary of detailed information that should be recorded together with the result

		"""
		resultKey = resultKey.strip()

		# check for correct format for result key
		if '  ' in resultKey:
			raise Exception ('Invalid resultKey - contains double space "  ": %s' % resultKey)
		if re.compile(r'.*\d{4}[-/]\d{2}[-/]\d{2}\ \d{2}[:/]\d{2}[:/]\d{2}.*').match(resultKey) != None :
			raise Exception ('Invalid resultKey - contains what appears to be a date time - which would imply alteration of the result key in each run: %s' % resultKey)
		if '\n' in resultKey:
			raise Exception ('Invalid resultKey - contains a new line: %s' % resultKey)
		if '%s' in resultKey or '%d' in resultKey or '%f' in resultKey: # people do this without noticing sometimes
			raise Exception('Invalid resultKey - contains unsubstituted % format string: '+resultKey)

		if isstring(value): value = float(value)
		assert isinstance(value, int) or isinstance(value, float), 'invalid type for performance result: %s'%(repr(value))

		if unit in self.unitAliases: unit = self.unitAliases[unit]
		assert isinstance(unit, PerformanceUnit), repr(unit)

		# toleranceStdDevs - might add support for specifying a global default in project settings
		resultDetails = resultDetails or []
		if isinstance(resultDetails, list):
			resultDetails = collections.OrderedDict(resultDetails)

		testobj.log.info("Performance result: %s = %s %s (%s)", resultKey, self.valueToDisplayString(value), unit,
						 'bigger is better' if unit.biggerIsBetter else 'smaller is better',
						 extra = BaseLogFormatter.tag(LOG_TEST_PERFORMANCE, [0,1]))
		with self._lock:
			prevresult = self.__previousResultKeys.get(resultKey, None)
			d = collections.OrderedDict(resultDetails)
			d['testId'] = testobj.descriptor.id
			if prevresult:
				previd, prevcycle, prevdetails = prevresult
				# if only difference is cycle (i.e. different testobj but same test id) then allow, but
				# make sure we report error if this test tries to report same key more than once, or if it
				# overlaps with another test's result keys
				if previd == testobj.descriptor.id and prevcycle==testobj.testCycle:
					testobj.addOutcome(BLOCKED, 'Cannot report performance result as resultKey was already used by this test: "%s"'%(resultKey))
					return
				elif previd != testobj.descriptor.id: 
					testobj.addOutcome(BLOCKED, 'Cannot report performance result as resultKey was already used - resultKey must be unique across all tests: "%s" (already used by %s)'%(resultKey, previd))
					return
				elif prevdetails != d: 
					# prevent different cycles of same test with different resultdetails 
					testobj.addOutcome(BLOCKED, 'Cannot report performance result as resultKey was already used by a different cycle of this test with different resultDetails - resultKey must be unique across all tests and modes: "%s" (this test resultDetails: %s; previous resultDetails: %s)'%(resultKey, list(d.items()), list(prevdetails.items()) ))
					return
			else:
				self.__previousResultKeys[resultKey] = (testobj.descriptor.id, testobj.testCycle, d)

		if testobj.getOutcome().isFailure():
			testobj.log.warning('   Performance result "%s" will not be recorded as test has failed', resultKey)
			return


		formatted = self.formatResult(testobj, value, resultKey, unit, toleranceStdDevs, resultDetails)
		self.recordResult(formatted, testobj)

	def formatResult(self, testobj, value, resultKey, unit, toleranceStdDevs, resultDetails):
		"""Retrieve an object representing the specified arguments that will be passed to recordResult to be written to the performance file(s).

		:param testobj: the test case instance registering the value
		:param value: the value to be reported
		:param resultKey: a unique string that fully identifies what was measured
		:param unit: identifies the unit the value is measured in
		:param toleranceStdDevs: indicates how many standard deviations away from the mean for a regression
		:param resultDetails:  A dictionary of detailed information that should be recorded together with the result

		"""
		data = {'resultKey':resultKey,
				'testId':testobj.descriptor.id,
				'value':str(value),
				'unit':str(unit),
				'biggerIsBetter':str(unit.biggerIsBetter).upper(),
				'toleranceStdDevs':str(toleranceStdDevs) if toleranceStdDevs else '',
				'samples':'1',
				'stdDev':'0' ,
				'resultDetails':resultDetails
				}
		return CSVPerformanceFile.toCSVLine(data)+'\n'

	def recordResult(self, formatted, testobj):
		"""Record results to the performance summary file.

		:param formatted: the formatted string to write
		:param testobj: object reference to the calling test

		"""
		# generate a file in the test output directory for convenience/triaging, plus add to the global summary
		path = testobj.output+'/performance_results.csv'
		encoding = None if PY2 else 'utf-8'
		
		def callGetRunHeader():
			try:
				return self.getRunHeader(testobj)
			except Exception: # for pre-2.0 signature
				return self.getRunHeader()
		
		if not os.path.exists(path):
			with openfile(path, 'w', encoding=encoding) as f:
				f.write(callGetRunHeader())
		with openfile(path, 'a', encoding=encoding) as f:
			f.write(formatted)
		
		# now the global one
		path = self.getRunSummaryFile(testobj)
		mkdir(os.path.dirname(path))
		with self._lock:
			alreadyexists = os.path.exists(toLongPathSafe(path))
			with openfile(path, 'a', encoding=encoding) as f:
				if not alreadyexists: 
					testobj.log.info('Creating performance summary log file at: %s', os.path.normpath(path))
					f.write(callGetRunHeader())
				f.write(formatted)
			self.__summaryFilesWritten.add(path)
	

class CSVPerformanceFile(object):
	"""Object to hold the model for a CSV performance file.

	If this file contains aggregated results the number of "samples" may be greater than 1 and the "value"
	will specify the mean result.

	:ivar dict ~.runDetails: A dictionary containing (string key, string value) information about the whole test run.
	
	:ivar list ~.results: A list where each item is a dictionary containing information about a given result, 
		containing values for each of the keys in L{COLUMNS}, for example 'resultKey', 'value', etc. 
		
	:ivar str ~.RUN_DETAILS: The constant prefix identifying information about the whole test run
	
	:ivar str ~.RESULT_DETAILS: The constant prefix identifying detailed information about a given result
	
	:ivar list ~.COLUMNS: Constant list of the columns in the performance output

	:param str contents: A string containing the contents of the file to be parsed (can be empty)

	"""
	COLUMNS = ['resultKey','testId','value','unit','biggerIsBetter','toleranceStdDevs','samples','stdDev']
	RUN_DETAILS = '#runDetails:#'
	RESULT_DETAILS = '#resultDetails:#'

	@staticmethod
	def aggregate(files):
		"""Aggregate a list of performance file objects into a single performance file object.

		Takes a list of one or more CSVPerformanceFile objects and returns a single aggregated
		CSVPerformanceFile with a single row for each resultKey (with the "value" set to the
		mean if there are multiple results with that key, and the stdDev also set appropriately).

		:param files: the list of performance file objects to aggregate

		"""
		if isinstance(files, CSVPerformanceFile): files = [files]
		details = collections.OrderedDict() # values are lists of unique run detail values from input files
		results = {}
		for f in files:
			if not f.results: continue # don't even include the rundetails if there are no results
			for r in f.results:
				if r['resultKey'] not in results:
					results[r['resultKey']] = collections.OrderedDict(r)
					# make it a deep copy
					results[r['resultKey']]['resultDetails'] = collections.OrderedDict( results[r['resultKey']].get('resultDetails', {}))
				else:
					e = results[r['resultKey']] # existing result which we will merge the new data into

					# calculate new mean and stddev
					combinedmean = (e['value']*e['samples'] + r['value']*r['samples']) / (e['samples']+r['samples'])

					# nb: do this carefully to avoid subtracting large numbers from each other
					# also we calculate the sample standard deviation (i.e. using the bessel-corrected unbiased estimate)
					e['stdDev'] = math.sqrt(
						((e['samples']-1)*(e['stdDev']**2)
						 +(r['samples']-1)*(r['stdDev']**2)
						 +e['samples']*( (e['value']-combinedmean) ** 2 )
						 +r['samples']*( (r['value']-combinedmean) ** 2 )
						 ) / (e['samples'] + r['samples'] - 1)
					)
					e['value'] = combinedmean
					e['samples'] += r['samples']
					e['resultDetails'] = r.get('resultDetails', {}) # just use latest; shouldn't vary

			for k in f.runDetails:
				if k not in details:
					details[k] = []
				if f.runDetails[k] not in details[k]:
					details[k].append(f.runDetails[k])

		a = CSVPerformanceFile('')
		for rk in sorted(results):
			a.results.append(results[rk])
		a.results.sort(key=lambda r: r['resultKey'])
		for k in details:
			a.runDetails[k] = '; '.join(sorted(details[k]))
		return a

	@staticmethod
	def toCSVLine(values):
		"""Convert a list or dictionary of input values into a CSV string.

		Note that no new line character is return in the CSV string. The input values can either be
		a list (any nested dictionaries are expanded into KEY=VALUE entries), or a dictionary (or OrderedDict)
		whose keys will be added in the same order as COLUMNS.

		:param values: the input list or dictionary

		"""
		if isinstance(values, list):
			items = []
			for v in values:
				if isinstance(v, dict):
					for k in v:
						items.append('%s=%s'%(k.replace('=','-').strip(), str(v[k]).replace('=','-').strip()))
				else:
					items.append(v)
			
			return ','.join([v.replace(',', ';').replace('"', '_').strip() for v in items])

		elif isinstance(values, dict):
			l = []
			for k in CSVPerformanceFile.COLUMNS:
				l.append(str(values.get(k,'')))
			if values.get('resultDetails', None):
				l.append(CSVPerformanceFile.RESULT_DETAILS)
				for k in values['resultDetails']:
					l.append('%s=%s'%(k, values['resultDetails'][k]))
			return CSVPerformanceFile.toCSVLine(l)

		else:
			raise Exception('Unsupported input type: %s'%values.__class__.__name__)
		
	def __init__(self, contents):
		header = None
		self.results = []
		self.runDetails = None
		for l in contents.split('\n'):
			l = l.strip()
			if not l: continue
			try:
				if not header:
					header = []
					assert l.startswith('#')
					for h in l.strip().split(','):
						h = h.strip()
						if h== self.RUN_DETAILS:
							self.runDetails = collections.OrderedDict()
						elif self.runDetails != None:
							h = h.split('=', 1)
							self.runDetails[h[0].strip()] = h[1].strip()
						else:
							h = h.strip('#').strip()
							if h: header.append(h)
				elif l.startswith('#'): continue
				else:
					row = l.split(',')
					r = collections.OrderedDict()
					for i in range(len(header)):
						if i >= len(row):
							raise Exception('Missing value for column "%s"'%header[i])
						else:
							val = row[i].strip()
							if header[i] in ['value', 'toleranceStdDevs', 'stdDev']:
								val = float(val or '0')
							elif header[i] in ['samples']:
								val = int(val  or '0')
							elif header[i] in ['biggerIsBetter']:
								val = True if val.lower()=='true' else False
							r[header[i]] = val
					resultDetails = None
					result = collections.OrderedDict()
					for i in range(0, len(row)):
						row[i] = row[i].strip()
						if row[i] == self.RESULT_DETAILS:
							resultDetails = collections.OrderedDict()
						elif resultDetails != None:
							d = row[i].split('=',1)
							resultDetails[d[0].strip()] = d[1].strip()
					
					if resultDetails == None: resultDetails = collections.OrderedDict()
					r['resultDetails'] = resultDetails
					self.results.append(r)
			except Exception as e:
				raise Exception('Cannot parse performance line - %s (%s): "%s"'%(e, e.__class__.__name__, l))
		
		if self.runDetails == None: self.runDetails = collections.OrderedDict()

	def __maybequote(self, s):
		return '"%s"' % s if isstring(s) else s
		
	def __str__(self):
		return 'CSVPerformanceFile< %d results; runDetails: %s>'%(len(self.results), ', '.join([('%s=%s'%(k, self.__maybequote(self.runDetails[k]))) for k in self.runDetails]))

	def __repr__(self):
		return 'CSVPerformanceFile<runDetails: %s%s\n>'%(', '.join([('%s="%s"'%(k, self.runDetails[k])) for k in self.runDetails]),
			''.join([('\n - %s'%(', '.join([('%s=%s'%(k, self.__maybequote(r.get(k, r.get('resultDetails',{}).get(k,None))))) for k in list(r.keys())+list(r.get('resultDetails',{}).keys()) if k!='resultDetails']))) for r in self.results]))



if __name__ == "__main__":
	USAGE = """
python -m pysys.utils.perfreporter aggregate PATH1 PATH2... > aggregated.csv

where PATH is a .csv file or directory of .csv files. 

The aggregate command combines the specifies file(s) to form a single file 
with one row for each resultKey, with the 'value' equal to the mean of all 
values for that resultKey and the 'stdDev' updated with the standard deviation. 
This can also be used with one or more .csv file to aggregate results from multiple 
cycles. 

"""
	# could later add support for automatically comparing files
	args = sys.argv[1:]
	if '-h' in sys.argv or '--help' in args or len(args) <2 or args[0] not in ['aggregate']:
		sys.stderr.write(USAGE)
		sys.exit(1)
	
	cmd = args[0]
	
	paths = []
	for p in args[1:]:
		if os.path.isfile(p):
			paths.append(p)
		elif os.path.isdir(p):
			for (dirpath, dirnames, filenames) in os.walk(p):
				for f in sorted(filenames):
					if f.endswith('.csv'):
						paths.append(dirpath+'/'+f)
		else:
			raise Exception('Cannot find file: %s'%p)
	
	if not paths:
		raise Exception('No .csv files found')
	files = []
	for p in paths:
		with openfile(p, encoding='utf-8') as f:
			files.append(CSVPerformanceFile(f.read()))
	
	if cmd == 'aggregate':
		f = CSVPerformanceFile.aggregate(files)
		sys.stdout.write('# '+CSVPerformanceFile.toCSVLine(CSVPerformanceFile.COLUMNS+[CSVPerformanceFile.RUN_DETAILS, f.runDetails])+'\n')
		for r in f.results:
			sys.stdout.write(CSVPerformanceFile.toCSVLine(r)+'\n')
