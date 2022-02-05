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

Some reporter classes are provided in the box, and the `BasePerformanceReporter` class can be used to create more. 
"""

import collections, threading, time, math, sys, os
import io
import logging

if __name__ == "__main__":
	sys.path.append(os.path.dirname( __file__)+'/../..')

from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *

log = logging.getLogger('pysys.perfreporter')

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

class PerformanceRunData:
	"""
	Holds performance data for a single test run, consistenting of runDetails and a list of performance results covering 
	one or more cycles. 
	
	:ivar dict[str,str] ~.runDetails: A dictionary containing (string key, string value) information about the whole test 
		run, for example operating system and hostname.
	
	:ivar list[dict] ~.results: A list where each item is a dictionary containing information about a given result. 
		The current keys are: resultKey, testId, value, unit, biggerIsBetter, toleranceStdDevs, samples, stdDev, 
		resultDetails. 

	"""
	def __init__(self, runDetails, results):
		self.runDetails = runDetails
		self.results = results

	@staticmethod
	def aggregate(runs):
		"""Aggregate a list of multiple runs and/or cycles into a single performance run data object with a single 
		entry for each unique resultKey with the value given as a mean of all the observed samples.

		:param list[PerformanceRunData] files: the list of run objects to aggregate.

		"""
		if isinstance(runs, PerformanceRunData): runs = [runs]
		
		details = {} # values are lists of unique run detail values from input files
		results = {}
		for f in runs:
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

		return PerformanceRunData(
			{k: '; '.join(sorted(details[k])) for k in details},
			sorted(list(results.values()), key=lambda r: r['resultKey'])
			)

class BasePerformanceReporter:
	"""API base class for creating a reporter that handles or stores performance results for later analysis.
	
	Each performance result consists of a value, a result key (which must 
	be unique across all test cases and modes, and also stable across different 
	runs), and a unit (which also encodes whether bigger values are better or worse). 
	Each test can report any number of performance results. 
	
	Performance reporter implementations are required to be thread-safe.
	 
	Project configuration of performance reporters is through the PySys project XML file using the 
	``<performance-reporter>`` tag. Multiple reporters may be configured and their individual properties set through the 
	nested ``<property>`` tag or XML attributes. Properties are set as Python attributes on the instance just after 
	construction, with automatic conversion of type to match the default value if specified as a static attribute on the 
	class. 
	
	If no reporters are explicitly configured, default reporters will be added. 

	:ivar pysys.config.project.Project project: The project configuration instance.
	
	:ivar str testoutdir: The output directory used for this test run 
		(equal to `runner.outsubdir`), an identifying string which often contains 
		the platform, or when there are multiple test runs on the same machine 
		may be used to distinguish between them. This is usually a relative path 
		but may be an absolute path. 
		
	:ivar runner: A reference to the runner. 
	
	.. version added:: 2.1
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
		
		# anything listed here can be passed using just a string literal
		self.unitAliases = {
			's':PerformanceUnit.SECONDS, 
			'ns':PerformanceUnit.NANO_SECONDS, 
			'/s': PerformanceUnit.PER_SECOND
			}
			
	def setup(self, **kwargs):
		"""
		Called before any tests begin to prepare the performance writer for use, once the runner is setup, and any project 
		configuration properties for this performance reporter have been assigned to this instance. 
		
		Usually there is no reason to override the constructor, and any initialization can be done in this method. 
		
		.. version added:: 2.1
		"""
		pass
		
	def getRunDetails(self, testobj=None, **kwargs):
		"""Return an dictionary of information about this test run (e.g. hostname, start time, etc).
		
		Overriding this method is discouraged; customization of the run details should usually be performed by changing 
		the ``runner.runDetails`` dictionary from the `pysys.baserunner.BaseRunner.setup()` method. 

		:param testobj: the test case instance registering the value

		.. versionchanged:: 2.0 Added testobj parameter, for advanced cases where you want to 
		to provide different ``runDetails`` based on some feature of the test object or mode. 
		
		"""
		return collections.OrderedDict(self.runner.runDetails)
	
	def valueToDisplayString(self, value):
		"""Pretty-print an integer or float value to a moderate number of significant figures.

		The method additionally adds a "," grouping for large numbers.

		:param value: the value to be displayed, which must be a numeric type. 

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
		summaryfile = self.summaryfile or self.summaryFile or self.DEFAULT_SUMMARY_FILE
		
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

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		"""Report a performance result, with an associated unique key that identifies it.

		:param testobj: the test case instance registering the value. Use ``testobj.descriptor.id`` to get the ``testId``. 
		:param int|float value: the value to be reported. This may be an int or a float. 
		:param str resultKey: a unique string that fully identifies what was measured.
		:param PerformanceUnit unit: identifies the unit the value is measured in.
		:param float toleranceStdDevs: indicates how many standard deviations away from the mean for a regression.
		:param dict[str,obj] resultDetails:  A dictionary of detailed information that should be recorded together with the result.

		"""
		pass
		

	def cleanup(self):
		"""Called when PySys has finished executing tests.
		
		This is where any file footer and other I/O finalization can be written to the end of performance log files, and 
		is also a good time to do any required aggregation, printing of summaries or artifact publishing. 
		"""
		pass

class CSVPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which writes to a CSV file.
	
	This reporter writes to a UTF-8 file of 
	comma-separated values that is both machine and human readable and 
	easy to view and use in any spreadsheet program, and after the columns containing 
	the information for each result, contains comma-separated metadata containing 
	key=value information about the entire run (e.g. hostname, date/time, etc), 
	and (optionally) associated with each individual test result (e.g. test mode etc). 
	The per-run and per-result metadata is not arranged in columns since the structure 
	differs from row to row.

	After tests have run, the summary file is published with category ``CSVPerformanceReport`` 
	using the `pysys.writer.api.ArtifactPublisher` interface. 

	The following properties can be set in the project configuration for this reporter:		
	
	"""
	
	summaryFile = ''
	"""
	The filename pattern used for the summary file(s). 
	
	For compatibility purposes, if not specified explicitly, the summary file for the CSVPerformanceReporter can be 
	configured with the project property ``csvPerformanceReporterSummaryFile``, however this is deprecated. 
	This property can also be accessed and configured under the alternative capitalization ``summaryfile``, however this 
	is discouraged as of PySys 2.1+, where ``summaryFile`` is the preferred name. 

	"""

	aggregateCycles = True
	"""
	By default PySys will automatically rewrite the summary file at the end of a multi-cycle test with an aggregated 
	file containing the mean and standard deviation for all the samples, rather than a separate line for each one. 
	This is usually much easier to consume when triaging performance results and looking for regressions. 
	
	This behaviour can be disabled by setting ``aggregateCycles`` to ``False``. 
	
	.. versionadded:: 2.1
	"""

	publishArtifactCategory = 'CSVPerformanceReport' 
	"""
	If specified, the output file will be published as an artifact using the specified category name. 

	.. versionadded:: 2.1
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.csv'
	"""The default summary file if not overridden by the ``csvPerformanceReporterSummaryFile`` project property, or 
	the ``summaryfile=`` attribute. See `getRunSummaryFile()`. This is relative to the runner output+'/..' directory 
	(typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def setup(self, **kwargs):
		"""
		Called before any tests begin to prepare the performance writer for use, once the runner is setup, and any project 
		configuration properties for this performance reporter have been assigned to this instance. 
		
		Usually there is no reason to override the constructor, and any initialization can be done in this method. 
		
		.. version added:: 2.1
		"""
		self.__summaryFilesWritten = set()
		
		# for backwards compat - must do this before super.setup sets the summaryfile
		self.summaryfile = self.summaryfile or self.summaryFile or getattr(self.project, 'csvPerformanceReporterSummaryFile', '') or self.DEFAULT_SUMMARY_FILE
		
		super().setup()

	def getRunHeader(self, testobj=None, **kwargs):
		"""Return the header string to the CSV file.
		
		There should usually be no reason to override this method. 
		"""
		
		try:
			runDetails = self.getRunDetails(testobj)
		except Exception: # for pre-2.0 signature
			runDetails = self.getRunDetails()
		
		return CSVPerformanceFile.makeCSVHeaderLine(runDetails)

	def cleanup(self):
		with self._lock:
			if self.runner is not None and self.__summaryFilesWritten:
				for p in sorted(list(self.__summaryFilesWritten)):
					
					if self.runner.cycle > 1 and self.aggregateCycles:
						try:
							perfFile = CSVPerformanceFile.load(p)
							perfFile = CSVPerformanceFile.aggregate([perfFile])
						except Exception as ex:
							log.exception('Failed to read and aggregate performance information for %s: '%p)
							# Don't make it fatal, more useful to go ahead and publish it as best we can
						else:
							log.info('Rewriting CSV to aggregate results across all %d cycles'%self.runner.cycles)
							perfFile.dump(p)
				
					if self.publishArtifactCategory:
						self.runner.publishArtifact(p, self.publishArtifactCategory)

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		formatted = self.formatResult(testobj, value, resultKey, unit, toleranceStdDevs, resultDetails)
		self.recordResult(formatted, testobj)

	def printPerfSummary(self, **kwargs):
		""" Use the logger to print a summary of all performance results at the end of the test run. 
		
		Called by the runner (on the primary performance reporter) just after `cleanup`, 
		i.e. when all results have been finalized. 
		"""
		with self._lock:
			if not self.__summaryFilesWritten: return # nothing to do
			
			logger = logging.getLogger('pysys.perfreporter.summary')
			for p in sorted(list(self.__summaryFilesWritten)):
				perfFile = CSVPerformanceFile.load(p)
				perfFile = CSVPerformanceFile.aggregate([perfFile])
				
				if not perfFile.results: continue
				logger.info('Summary of performance results written to %s :', os.path.normpath(p).replace(os.path.normpath(self.project.testRootDir), '').lstrip('/\\'))
				for r in sorted(perfFile.results, key=lambda r: r['resultKey']):
					logger.info("  %s = %s %s (%s)%s", r['resultKey'], self.valueToDisplayString(r['value']), r['unit'],
						 'bigger is better' if r['biggerIsBetter'] else 'smaller is better',
							'' if r['samples']==1 else ', stdDev = '+self.valueToDisplayString(r['stdDev']),
								extra = BaseLogFormatter.tag(LOG_TEST_PERFORMANCE, [0,1]))

				logger.info('')
				
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
		encoding = 'utf-8'
		
		def callGetRunHeader():
			try:
				return self.getRunHeader(testobj)
			except Exception: # for pre-2.0 signature
				return self.getRunHeader()
		
		if not os.path.exists(path):
			with io.open(toLongPathSafe(path), 'w', encoding=encoding) as f:
				f.write(callGetRunHeader())
		with io.open(toLongPathSafe(path), 'a', encoding=encoding) as f:
			f.write(formatted)
		
		# now the global one
		path = self.getRunSummaryFile(testobj)
		mkdir(os.path.dirname(path))
		with self._lock:
			alreadyexists = os.path.exists(toLongPathSafe(path))
			with io.open(toLongPathSafe(path), 'a', encoding=encoding) as f:
				if not alreadyexists: 
					testobj.log.info('Creating performance summary log file at: %s', os.path.normpath(path))
					f.write(callGetRunHeader())
				f.write(formatted)
			self.__summaryFilesWritten.add(path)
	

class CSVPerformanceFile(PerformanceRunData):
	"""Object to hold the model for a CSV performance file.

	If this file contains aggregated results the number of "samples" may be greater than 1 and the "value"
	will specify the mean result.

	:ivar dict[str,obj] ~.runDetails: A dictionary containing (string key, string value) information about the whole test run.
	
	:ivar list[dict] ~.results: A list where each item is a dictionary containing information about a given result, 
		containing values for each of the keys in L{COLUMNS}, for example 'resultKey', 'value', etc. 
		
	:ivar str ~.RUN_DETAILS: The constant prefix identifying information about the whole test run
	
	:ivar str ~.RESULT_DETAILS: The constant prefix identifying detailed information about a given result
	
	:ivar list[str] ~.COLUMNS: Constant list of the columns in the performance output

	:param str contents: A string containing the contents of the file to be parsed (can be empty)
	:rtype: CSVPerformanceFile
	"""
	COLUMNS = ['resultKey','testId','value','unit','biggerIsBetter','toleranceStdDevs','samples','stdDev']
	RUN_DETAILS = '#runDetails:#'
	RESULT_DETAILS = '#resultDetails:#'

	@staticmethod
	def aggregate(files):
		"""Aggregate a list of performance file objects into a single CSVPerformanceFile object.

		Takes a list of one or more CSVPerformanceFile objects and returns a single aggregated
		CSVPerformanceFile with a single row for each resultKey (with the "value" set to the
		mean if there are multiple results with that key, and the stdDev also set appropriately).

		This method is now deprecated in favour of `PerformanceRunData.aggregate`. 

		:param list[CSVPerformanceFile] files: the list of performance file objects to aggregate.

		"""
		if isinstance(files, CSVPerformanceFile): files = [files]
		
		agg = PerformanceRunData.aggregate([f for f in files])
		
		result = CSVPerformanceFile('')
		result.results = agg.results
		result.runDetails = agg.runDetails
		return result

	@staticmethod
	def load(src):
		"""
		Read the runDetails and results from the specified .csv file on disk.
		
		:str src: The path to read. 
		:returns: A new `CSVPerformanceFile` instance. 
		
		.. versionadded:: 2.1
		"""
		with io.open(toLongPathSafe(src), 'r', encoding='utf-8') as f:
			return CSVPerformanceFile(f.read())
				
	def dump(self, dest):
		"""
		Dump the runDetails and results from this object to a CSV at the specified location. 
		
		Any existing file is overwritten. 
		
		:str dest: The destination path to write to. 
		
		.. versionadded:: 2.1
		"""
		with io.open(toLongPathSafe(dest), 'w', encoding='utf-8') as f:
			f.write(self.makeCSVHeaderLine(self.runDetails))
			for v in self.results:
				f.write(self.toCSVLine(v)+'\n')

	@staticmethod 
	def makeCSVHeaderLine(runDetails):
		return '# '+CSVPerformanceFile.toCSVLine(CSVPerformanceFile.COLUMNS+[CSVPerformanceFile.RUN_DETAILS, runDetails])+'\n'

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
		with io.open(toLongPathSafe(os.path.abspath(p)), encoding='utf-8') as f:
			files.append(CSVPerformanceFile(f.read()))
	
	if cmd == 'aggregate':
		f = CSVPerformanceFile.aggregate(files)
		sys.stdout.write('# '+CSVPerformanceFile.toCSVLine(CSVPerformanceFile.COLUMNS+[CSVPerformanceFile.RUN_DETAILS, f.runDetails])+'\n')
		for r in f.results:
			sys.stdout.write(CSVPerformanceFile.toCSVLine(r)+'\n')
