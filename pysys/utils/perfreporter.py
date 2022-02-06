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
import json
import glob

if __name__ == "__main__":
	sys.path.append(os.path.dirname( __file__)+'/../..')

from pysys.constants import *
from pysys.utils.logutils import BaseLogFormatter
from pysys.utils.fileutils import mkdir, toLongPathSafe
from pysys.utils.pycompat import *
from pysys.utils.logutils import ColorLogFormatter, stdoutPrint

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
		assert not kwargs, kwargs.keys() # **kwargs allows constructor to be extended in future if needed; give error if any unexpected args are passed
		
		self.testoutdir = os.path.basename(testoutdir)
		self.summaryfile = summaryfile
		self.project = project
		self.hostname = HOSTNAME.lower().split('.')[0]
		if self.runner is not None: # just in case we're constructing it for standalone execution in the compare script
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
	
	@staticmethod
	def valueToDisplayString(value):
		"""Pretty-print an integer or float value to a moderate number of significant figures.

		The method additionally adds a "," grouping for large numbers.
		
		Subclasses may customize this if desired, including by reimplementing as a non-static method. 

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
	
	@staticmethod
	def tryDeserializePerformanceFile(self, path):
		"""
		Advanced method which allows performance reporters to deserialize the files they write to allow them to be used 
		as comparison baselines. 
		
		Most reporters do not need to worry about this method. 
		
		If you do implement it, return an instance of PerformanceRunData, or None if you do not support this file type, for 
		example because the extension does not match. It is best to declare this as a static method if possible. 
		
		:rtype: PerformanceRunData
		"""
		return None

class JSONPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which writes to a JSON file.
	
	After tests have run, the summary file is published with category ``JSONPerformanceReport`` 
	using the `pysys.writer.api.ArtifactPublisher` interface. 

	.. versionadded:: 2.1

	The following properties can be set in the project configuration for this reporter:		
	
	"""
	
	summaryFile = ''
	"""
	The ``.json`` filename pattern used for the summary file(s); see `DEFAULT_SUMMARY_FILE`. 
	"""

	publishArtifactCategory = 'JSONPerformanceReport' 
	"""
	If specified, the output file will be published as an artifact using the specified category name. 
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.json'
	"""The default summary file if not overridden by the ``summaryFile=`` attribute. See `getRunSummaryFile()`. 
	This is relative to the runner output+'/..' directory (typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def setup(self, **kwargs):
		super().setup()
		self.__summaryFilesWritten = set()
		
	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		path = self.getRunSummaryFile(testobj)
		mkdir(os.path.dirname(path))
		with self._lock:
			alreadyexists = os.path.exists(toLongPathSafe(path))
			with io.open(toLongPathSafe(path), 'a', encoding='utf-8') as f:
				if not alreadyexists: 
					testobj.log.info('Creating performance summary log file at: %s', os.path.normpath(path))
					f.write('{"runDetails": ')
					json.dump(self.getRunDetails(testobj), f)
					f.write(', "results":[\n')
				else:
					f.write(',\n')
					
				json.dump({
					'resultKey':resultKey,
					'value':value,
					'unit':str(unit),
					'biggerIsBetter':unit.biggerIsBetter,
					'samples':1,
					'stdDev':0,
					'toleranceStdDevs':toleranceStdDevs,
					'testId':testobj.descriptor.id,
					'resultDetails':resultDetails or {}
				}, f)
			self.__summaryFilesWritten.add(path)

	def cleanup(self):
		with self._lock:
			if self.__summaryFilesWritten:
				for p in sorted(list(self.__summaryFilesWritten)):
					with io.open(toLongPathSafe(p), 'a', encoding='utf-8') as f:
						f.write('\n]}\n')
					
					log.info('Performance results were written to: %s', os.path.normpath(p).replace(os.path.normpath(self.project.testRootDir), '').lstrip('/\\'))

					if self.publishArtifactCategory:
						self.runner.publishArtifact(p, self.publishArtifactCategory)

	@staticmethod
	def tryDeserializePerformanceFile(path):
		if not path.endswith('.json'): return None
		with io.open(toLongPathSafe(path), encoding='utf-8') as f:
			data = json.load(f)
			return PerformanceRunData(path, data['runDetails'], data['results'])

class PrintSummaryPerformanceReporter(BasePerformanceReporter):
	"""Performance reporter which logs a human-friendly summary of all performance results to the console at the end of 
	the test run. 

	By setting the `BASELINES_ENV_VAR` environment variable, this reporter will also print out an 
	automatic comparison from the named baseline file(s) to the results from the current test run. 
	This feature is very useful when comparingdifferent strategies for optimizing your application. 
	
	.. versionadded:: 2.1

	"""

	BASELINES_ENV_VAR = 'PYSYS_PERFORMANCE_BASELINES'
	"""
	Set this environment variable to a comma-separated list of performance (e.g. ``.csv``) files to print out an 
	automatic comparison from the baseline file(s) to the results from the current test run. 
	
	This feature is very useful when comparing different strategies for optimizing your application. 
	
	For best results, use multiple cycles for all test runs so that standard deviation can be calculated. 
	
	The filenames can be absolute paths, glob paths using ``*`` and ``**``, or relative to the testRootDir. For example::
	
		export PYSYS_PERFORMANCE_BASELINES=__pysys_performance/mybaseline*/**/*.csv,__pysys_performance/optimization1*/**/*.csv
		
	"""

	def setup(self, **kwargs):
		super().setup()
		self.results = []
		
		self.comparisonGenerator = PerformanceComparisonGenerator(reporters=self.runner.performanceReporters)
		self.baselines = self.comparisonGenerator.loadFiles(
			baselineBaseDir=self.project.testRootDir,
			paths=os.getenv(self.BASELINES_ENV_VAR,'').split(','), 
			)
		log.info('Successfully loaded performance comparison data from %d files: %s', len(self.baselines), ', '.join(b.name for b in self.baselines))

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
		with self._lock:
			self.results.append({
						'resultKey':resultKey,
						'value':value,
						'unit':str(unit),
						'biggerIsBetter':unit.biggerIsBetter,
						'samples':1,
						'stdDev':0,
						'toleranceStdDevs':toleranceStdDevs,
						'testId':testobj.descriptor.id,
						'resultDetails':resultDetails or {}
					})

	def isEnabled(self, **kwargs):
		return True
	
	def cleanup(self):
		if not self.isEnabled(): return
		if not self.results: return
		
		with self._lock:
			logmethod = logging.getLogger('pysys.perfreporter.summary').info

			# perform aggregation in case there are multiple cycles
			p = PerformanceRunData.aggregate(PerformanceRunData('this', self.getRunDetails(), self.results))

			if not self.baselines:
				logmethod('Performance results summary:')
				# simple formatting when there's no comparisons to be done
				for r in p.results:
					logmethod("  %s = %s %s (%s)%s %s", r['resultKey'], self.valueToDisplayString(r['value']), r['unit'],
						 'bigger is better' if r['biggerIsBetter'] else 'smaller is better',
							'' if r['samples']==1 or ['value'] == 0 else f", stdDev={self.valueToDisplayString(r['stdDev'])} ({100.0*r['stdDev']/r['value']:0.1f}% of mean)",
							r['testId'],
								extra = BaseLogFormatter.tag(LOG_TEST_PERFORMANCE, [0,1], suppress_prefix=True))
				
			else:
				logmethod('\n')
				self.comparisonGenerator.logComparisons(self.baselines+[p])


class PerformanceComparisonGenerator:
	"""Internal helper class for comparing multiple .csv or json performance files and printing the differences. 

	:meta private: Not public API may change at any time. 
	.. versionadded:: 2.1

	"""

	BASELINES_ENV_VAR = PrintSummaryPerformanceReporter.BASELINES_ENV_VAR

	def __init__(self, reporters): 
		self.reporters = reporters # list of perf reporter instances (or for standalone invocation, classes); must be at least one
		
			# - with the static tryDeserializePerformanceFile method on them
			
		# We'd like to delegate to the first runner. Assuming it's a static method is probably reasonable. Could break if user subclass redefines as non-static
		self.valueToDisplayString = reporters[0].valueToDisplayString

	def loadFiles(self, baselineBaseDir, paths):
		# return a list PerformanceRunData for each path in the specified list
		
		configuredBaselines = os.getenv(self.BASELINES_ENV_VAR)
		if not paths:
			return None

		baselines = []
		for b in paths:
			b = b.strip()
			if not b: continue
			
			# if not abs, take paths as relative to testRootDir. Easier to work with the cwd which is constantly changing
			b = os.path.join(baselineBaseDir, b)
			
			if os.path.isfile(b): 
				baselines.append(b)
			else:
				globresults = sorted(glob.glob(b, recursive=True))
				if not globresults: raise Exception('Cannot find any paths matching '+self.BASELINES_ENV_VAR+' expression: %s'%b)
				baselines.extend(globresults)
		baselineData = {}
		for b in baselines:
			if os.path.isdir(b): raise Exception(self.BASELINES_ENV_VAR+' may contain "*" or "**" glob expressions but not directories: %s'%b)
			x = None
			for r in self.reporters:
				x = r.tryDeserializePerformanceFile(b)
				if x: break
			if x:
				baselineData[b] = x
			else:
				raise Exception('Failed to find a reporter that can deserialize performance files of this type: %s'%b)

		baselineData = [PerformanceRunData.aggregate(b) for b in baselineData.values()]
		return baselineData
		
	def logComparisons(self, comparisonFiles, sortby=None, printmethod=stdoutPrint):
		# comparisonFiles are a list of PerformanceRunData instances
		
		# NB: this method implementation mutates the passed in comparisonFiles
		
		sortby = sortby or os.getenv('PYSYS_PERFORMANCE_SORT_BY', 'resultKey')
		
		files = comparisonFiles

		out  = printmethod

		# we may not have the project available here if running this standalone, but can still reuse the same 
		# logic for deciding if coloring is enabled
		colorFormatter = ColorLogFormatter({})
		def addColor(category, s):
			if not category: return s
			return colorFormatter.formatArg(category, s) 
				
		# usually resultKey is itself the unique key, but for comparisons we also 
		# want to include units/biggerIsBetter since if these change the 
		# comparison would be invalidated
		ComparisonKey = collections.namedtuple('ComparisonKey', ['resultKey', 'unit', 'biggerIsBetter'])

		# iterate over each comparison item, stashing various aggregated information we need later, and printing summary info
		for p in files:
			p.keyedResults = {
				ComparisonKey(resultKey=r['resultKey'], unit=r['unit'], biggerIsBetter=r['biggerIsBetter'])
				: r for r in p.results
			}

		commonRunDetails = {}
		for k in list(files[-1].runDetails.keys()):
			if all([k in p.runDetails and  p.runDetails[k] == files[-1].runDetails[k] for p in files]):
				commonRunDetails[k] = files[-1].runDetails[k]

		def formatRunDetails(k, val):
			valsplit = val.split(';')
			if k == 'startTime' and len(valsplit)>=3:
				val = ' .. '.join([valsplit[0].strip(), valsplit[-1].strip()])
			else:
				val = val.replace('; ',';')
			return '%s=%s'%(k, addColor(LOG_TEST_DETAILS, val))

		#out('Comparing performance files with these common run details: %s'% ', '.join([formatRunDetails(k, commonRunDetails[k]) for k in commonRunDetails]))

		# Assign a comparison label to each; use outDirName if unique, else make something based on the filename
		if len(set(p.runDetails.get('outDirName') for p in files)) == len(files):
			for p in files: p.comparisonLabel = p.runDetails.get('outDirName', p.name)
		else:
			for p in files: p.comparisonLabel = os.path.splitext(os.path.basename(p.name))[0].replace('perf_','')
			
		out('Performance comparison summary between the following runs (the differing "run details" are shown):')
			
		for p in files:
			out('- %s (%d result keys, %d samples/result)%s:'%(
				addColor(LOG_TEST_DETAILS, p.comparisonLabel), 
				len(p.results), 
				float( sum([r['samples'] for r in p.results])) / len(p.results),
				'' if p.comparisonLabel != p.runDetails.get('outDirName')
					else f' from {p.name}'
				))
			out('     %s'%', '.join([formatRunDetails(k, p.runDetails[k]) for k in p.runDetails if k not in commonRunDetails]))

		out('')
		out('Comparison results:')
		out('  where format is (fromRun->toRun): (%improvement) = (change above 2 sigmas/stdDevs is 95% probability it\'s significant)')
		out('')
		ComparisonData = collections.namedtuple('ComparisonData', [
			'comparisonPercent', #%improvement
			'comparisonSigmas', # improvements as a multiple of stddec
			'ratio', # speedup ratio of from->to, how much faster we are now
			'rfrom', # the "from" value
			'rto',   # the "to"   value
			'relativeStdDevTo', # relative stdDev as a % of the "to" value, or None if only one sample (or value is 0)
			])
		
		# now compute comparison info, comparing each path to the final one
		comparisons = {} # ComparisonKey:[ComparisonInfo or string if not available, ...]
		comparetoresults = files[-1].keyedResults
		comparisonheaders = []
		for p in files[:-1]:
			if len(files)>2:
				comparisonheaders.append('%s->%s'%(p.comparisonLabel, files[-1].comparisonLabel))
			
			keyedResults = p.keyedResults
			for k in comparetoresults:
				c = comparisons.setdefault(k, [])
				if k not in keyedResults:
					c.append('Compare from value is missing')
				else:
					rfrom = keyedResults[k]
					rto = comparetoresults[k]
					# avoid div by zero errors; results are nonsensical anyway if either is zero
					if rfrom['value'] == 0: 
						c.append('Compare from value is zero')
						continue
					if rto['value'] == 0: 
						c.append('Compare to value is zero')
						continue

					# how many times faster are we now
					ratio = rto['value']/rfrom['value']
					# use a + or - sign to indicate improvement vs regression
					sign = 1.0 if k.biggerIsBetter else -1.0
					
					# frequently at least one of these will have only one sample so 
					# not much point doing a statistically accurate stddev estimate; so just 
					# take whichever is bigger (which neatly ignores any that are zero due
					# to only one sample)
					stddevRatio = max(abs(rfrom['stdDev']/rfrom['value']), abs(rto['stdDev']/rto['value']))
					
					comparisonPercent = 100.0*(ratio - 1)*sign
					# assuming a normal distribution, 1.0 or more gives 68% confidence of 
					# a real difference, and 2.0 or more gives 95%
					comparisonSigmas = sign*((ratio-1)/stddevRatio) if stddevRatio else None
					
					c.append(ComparisonData(
						comparisonPercent=comparisonPercent, 
						comparisonSigmas=comparisonSigmas,
						ratio=ratio,
						rfrom=rfrom['value'], 
						rto=rto['value'],
						relativeStdDevTo=100.0*rto['stdDev']/rto['value'] if rto['samples'] > 0 and rto['value']!=0 else None,
					))

		if comparisonheaders:
			headerpad = max([len(h) for h in comparisonheaders])
			comparisonheaders = [('%'+str(headerpad+1)+'s')%(h+':') for h in ([files[-1].comparisonLabel]+comparisonheaders)]

		def getComparisonKey(k):
			if sortby == 'resultKey': return k
			if sortby == 'testId': return (allresultinfo[k]['testId'], k)
			# sort with regressions at the bottom, so they're more prominent
			if sortby == 'comparison%': return [
					(-1*c.comparisonPercent) if hasattr(c, 'comparisonPercent') else -10000000.0
					for c in comparisons[k]]+[k]
			raise Exception(f'Invalid sortby key "{sortby}"; valid values are: resultKey, testId, comparison%')

		def addPlus(s):
			if not s.startswith('-'): return '+'+s
			return s

		sortedkeys = sorted(comparisons.keys(), key=getComparisonKey)
		
		for k in sortedkeys:
			out('%s from %s'%(colorFormatter.formatArg(LOG_TEST_PERFORMANCE, k.resultKey), files[-1].keyedResults[k]['testId']))
			
			r = files[-1].keyedResults[k]
			out(' '+f"Mean from this run = {self.valueToDisplayString(r['value'])} {r['unit']}"+
							('' if r['samples']==1 or ['value'] == 0 else f" with stdDev={self.valueToDisplayString(r['stdDev'])} ({100.0*r['stdDev']/r['value']:0.1f}% of mean)"),
					)

			i = 0
			for c in comparisons[k]:
				i+=1
				prefix = ('%s '%comparisonheaders[i]) if comparisonheaders else ''
				if not hasattr(c, 'comparisonPercent'):
					# strings for error messages
					out('  '+prefix+c)
					continue
				
				if c.comparisonSigmas != None:
					significantresult = abs(c.comparisonSigmas) >= (files[-1].keyedResults[k].get('toleranceStdDevs', 0.0) or 2.0)
				else:
					significantresult = abs(c.comparisonPercent) >= 10
				category = None
				if significantresult:
					category = LOG_PERF_BETTER if c.comparisonPercent > 0 else LOG_PERF_WORSE
				
				if c.comparisonSigmas is None:
					sigmas = ''
				else:
					sigmas = ' = %s sigmas'%addColor(category, addPlus('%0.1f'%c.comparisonSigmas))
				
				line = '  '+prefix+'%s%s'%(
					addColor(category, '%6s'%(addPlus('%0.1f'%c.comparisonPercent)+'%')), 
					sigmas, 
					)
				"""if i==len(comparisons):
					line +=  ' ( -> %s %s%s )'%(
						self.valueToDisplayString(c.rto), 
						files[-1].keyedResults[k]['unit'],
						'' if c.relativeStdDevTo in (None, 0.0) else
							f'; stdDev {c.relativeStdDevTo:0.1f}% of mean'
					)
				"""
				out(line)
			out('')
		

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
	The filename pattern used for the summary file(s); see `DEFAULT_SUMMARY_FILE`. 
	
	For compatibility purposes, if not specified explicitly, the summary file for the CSVPerformanceReporter can be 
	configured with the project property ``csvPerformanceReporterSummaryFile``, however this is deprecated. 
	This property can also be accessed and configured under the alternative capitalization ``summaryfile``, however this 
	is discouraged as of PySys 2.1+, where ``summaryFile`` is the preferred name. 

	"""

	aggregateCycles = False
	"""
	Enable this if you want PySys to rewrite the summary file at the end of a multi-cycle test with an aggregated 
	file containing the mean and standard deviation for all the cycles, rather than a separate line for each cycle. 
	This may be easier to consume when triaging performance results and looking for regressions. 
	
	.. versionadded:: 2.1
	"""

	publishArtifactCategory = 'CSVPerformanceReport' 
	"""
	If specified, the output file will be published as an artifact using the specified category name. 

	.. versionadded:: 2.1
	"""

	DEFAULT_SUMMARY_FILE = '__pysys_performance/${outDirName}_${hostname}/perf_${startDate}_${startTime}.${outDirName}.csv'
	"""The default summary file if not overridden by the ``csvPerformanceReporterSummaryFile`` project property, or 
	the ``summaryFile=`` attribute. See `getRunSummaryFile()`. This is relative to the runner output+'/..' directory 
	(typically testRootDir, unless ``--outdir`` is overridden).
	"""

	def setup(self, **kwargs):
		super().setup()

		# for backwards compat
		self.summaryfile = self.summaryfile or self.summaryFile or getattr(self.project, 'csvPerformanceReporterSummaryFile', '') or self.DEFAULT_SUMMARY_FILE

		self.__summaryFilesWritten = set()

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
				
					log.info('Performance results were written to: %s', os.path.normpath(p).replace(os.path.normpath(self.project.testRootDir), '').lstrip('/\\'))
					log.info('  (add the above path to env %s to show a comparison against that baseline on future test runs)', PrintSummaryPerformanceReporter.BASELINES_ENV_VAR)
					
					if self.publishArtifactCategory:
						self.runner.publishArtifact(p, self.publishArtifactCategory)

	def reportResult(self, testobj, value, resultKey, unit, toleranceStdDevs=None, resultDetails=None):
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
	
	@staticmethod
	def tryDeserializePerformanceFile(path):
		if not path.endswith('.csv'): return None
		return CSVPerformanceFile.load(path)

class PerformanceRunData:
	"""
	Holds performance data for a single test run, consistenting of runDetails and a list of performance results covering 
	one or more cycles. 
	
	:ivar str name: The name, typically a filename. 
	
	:ivar dict[str,str] ~.runDetails: A dictionary containing (string key, string value) information about the whole test 
		run, for example operating system and hostname.
	
	:ivar list[dict] ~.results: A list where each item is a dictionary containing information about a given result. 
		The current keys are: resultKey, testId, value, unit, biggerIsBetter, toleranceStdDevs, samples, stdDev, 
		resultDetails. 

	"""
	def __init__(self, name, runDetails, results):
		self.name = name
		self.runDetails = runDetails
		self.results = results

	def __maybequote(self, s):
		return '"%s"' % s if isstring(s) else s
	def __str__(self):
		return 'PerformanceRunData< %d results; runDetails: %s>'%(len(self.results), ', '.join([('%s=%s'%(k, self.__maybequote(self.runDetails[k]))) for k in self.runDetails]))
	def __repr__(self):
		return 'PerformanceRunData<runDetails: %s%s\n>'%(', '.join([('%s="%s"'%(k, self.runDetails[k])) for k in self.runDetails]),
			''.join([('\n - %s'%(', '.join([('%s=%s'%(k, self.__maybequote(r.get(k, r.get('resultDetails',{}).get(k,None))))) for k in list(r.keys())+list(r.get('resultDetails',{}).keys()) if k!='resultDetails']))) for r in self.results]))

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
					# also we calculate the SAMPLE standard deviation (i.e. using the bessel-corrected unbiased estimate)
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
			', '.join(run.name or '?' for run in runs),
			{k: '; '.join(sorted(details[k])) for k in details},
			sorted(list(results.values()), key=lambda r: r['resultKey'])
			)


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
		result = CSVPerformanceFile('', name=agg.name)
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
			return CSVPerformanceFile(f.read(), name=src)
				
	def dump(self, dest):
		"""
		Dump the runDetails and results from this object to a CSV at the specified location. 
		
		Any existing file is overwritten. 
		
		:str dest: The destination path or file handle to write to. 
		
		.. versionadded:: 2.1
		"""
		if isinstance(dest, str):
			with io.open(toLongPathSafe(dest), 'w', encoding='utf-8') as f:
				return self.dump(f)
				
		dest.write(self.makeCSVHeaderLine(self.runDetails))
		for v in self.results:
			dest.write(self.toCSVLine(v)+'\n')

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
		
	def __init__(self, contents, name=None):
		super().__init__(name, None, [])
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

if __name__ == "__main__":
	USAGE = """
perfreporter.py aggregate PATH1 PATH2... > aggregated.csv
perfreporter.py compare PATH_GLOB1 PATH_GLOB2...

where PATH is a .csv file or directory of .csv files 
      GLOB_PATH is a path to a file or files, optionally containing by * and ** globs

The aggregate command combines the specifies CSVfile(s) to form a single file 
with one row for each resultKey, with the 'value' equal to the mean of all 
values for that resultKey and the 'stdDev' updated with the standard deviation. 
This can also be used with one or more .csv file to aggregate results from multiple 
cycles. 

The compare command prints a comparison from each listed performance file to the final one in the list.
Note that the format of the output may change at any time, and it is not intended for machine parsing. 

"""
	# could later add support for automatically comparing files
	args = sys.argv[1:]
	if '-h' in sys.argv or '--help' in args or len(args) <2 or args[0] not in ['aggregate', 'compare']:
		sys.stderr.write(USAGE)
		sys.exit(1)
	
	cmd = args[0]
	
	# send log output to stderr to avoid interfering with output we might be redirecting to a file	
	logging.basicConfig(format='%(levelname)s: %(message)s', stream=sys.stderr, level=getattr(logging, os.getenv('PYSYS_LOG_LEVEL', 'INFO').upper()))
	
	if cmd == 'aggregate':
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

		f = CSVPerformanceFile.aggregate(files)
		f.dump(sys.stdout)
	elif cmd == 'compare':
		paths = args[1:]
		from pysys.config.project import Project

		project = Project.findAndLoadProject()
		# Can't easily get these classes from project without replicating the logic to instantiate them, which would 
		# be error prone
		performanceReporterClasses = [CSVPerformanceReporter, JSONPerformanceReporter]
		
		gen = PerformanceComparisonGenerator(performanceReporterClasses)
		files = gen.loadFiles(baselineBaseDir=project.testRootDir, paths=paths)
		gen.logComparisons(files)

